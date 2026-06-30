import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import math
import base64  
import os      

def carregar_imagem(caminho):
    """Verifica se a imagem é web ou local e a converte para base64 se necessário"""
    if caminho.startswith("http"):
        return caminho  # Se for link, retorna normal
    elif os.path.exists(caminho):
        # Se for arquivo local, converte para base64
        with open(caminho, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        
        extensao = caminho.split('.')[-1].lower()
        tipo_mime = "image/png" if extensao == "png" else "image/jpeg"
        
        return f"data:{tipo_mime};base64,{encoded}"
    else:
        return None 

# 1. Configuração da Página
st.set_page_config(
    page_title="Dashboard: DESAFIO GYMRATS!", 
    page_icon="🚀", 
    layout="wide" # O Streamlit adapta para 100% no mobile automaticamente
)

# 2. Cabeçalho
st.markdown("<h1 style='text-align: center;'>🚀 DESAFIO GYMRATS</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 16px;'>Competição para premiar quem será o mais ratoso de todos os ratos qui qui qui</p>", unsafe_allow_html=True)
st.divider()

# --- CRIANDO AS ABAS PRINCIPAIS ---
desafio1, desafio2 = st.tabs(["1° DESAFIO", "2° DESAFIO"], default="1° DESAFIO")


with desafio1:
    # --- CONFIGURAÇÃO DE DADOS GLOBAL ---
    dataCheckins_real = pd.read_excel('checkin_frequency_desafio1.xlsx', sheet_name='competitors')
    dataCheckins_fun = pd.read_excel('checkin_frequency_desafio1.xlsx', sheet_name='just_for_fun')

    competidores_reais = dataCheckins_real.columns[3:].tolist()
    total_weeks = dataCheckins_real.shape[0]

    # --- CONTROLES DE TOPO ---
    col_info, col_slider, col_toggle = st.columns([1, 3, 1])

    with col_info:
        st.markdown("<small><b>Início</b>: 25/01/2026<br><b>Término</b>: 27/06/2026<br><b>Duração</b>: 22 semanas</small>", unsafe_allow_html=True)

    with col_slider:
        last_week = st.slider(
            "Arraste para selecionar a semana final para análise:",
            min_value=1,
            max_value=total_weeks,
            value=total_weeks
        )

    with col_toggle:
        st.write("") 
        st.write("")
        incluir_fun = st.toggle("🎭 Incluir competidores 'Just for Fun'", value=True)

    if incluir_fun:
        colunas_extras = dataCheckins_fun.columns.difference(['week', 'date_start', 'date_end'])
        dataCheckins = pd.concat([dataCheckins_real, dataCheckins_fun[colunas_extras]], axis=1)
    else:
        dataCheckins = dataCheckins_real.copy()

    participantsNames = dataCheckins.columns[3:]
    initial_week = 1

    df_cumulative = dataCheckins[participantsNames].cumsum()

    coefficient_table = {0: 0.0, 1: 0.1, 2: 0.2, 3: 0.4, 4: 0.6, 5: 1.0}
    investimento_inicial = 100.0
    valor_por_semana = investimento_inicial / total_weeks
    windsor_cut = 3  

    photos = {
        "Lhucas": "./img/lhucas.jpg", 
        "Francis": "img/francis.jpg",
        "Félix": "img/felix.jpg",
        "Ariel": "img/ariel.jpg",
        "Elizabeth": "img/elizabeth.jpg",
        "Lara": "./img/sem-foto.png",
        "Bruna": "img/bruna.jpg",
        "Rafael":"img/rafael.jpg"
    }
        
    colors = {
        "Lhucas": "#0d6efd", "Francis": "#6f42c1", "Félix": "#fd7e14",
        "Ariel": "#20c997", "Elizabeth": "#198754", "Lara": "#e83e8c", "Bruna": "#ffc107"
    }

    # --- FUNÇÕES DE CÁLCULO ---
    def obter_janela_windsor(semana_atual, total_semanas, windsor_cut_max):
        """Calcula o tamanho progressivo do corte de Windsor baseado na semana atual"""
        inicio_cortes = total_semanas - 2 * (windsor_cut_max - 1)
        
        # Se ainda não chegou na semana de iniciar os cortes, a janela é 0
        if semana_atual < inicio_cortes or inicio_cortes < 1:
            return 0
            
        # Aumenta a janela em 1 a cada 2 semanas
        janela = 1 + (semana_atual - inicio_cortes) // 2
        
        # Garante que a janela nunca ultrapasse o limite máximo definido
        return min(janela, windsor_cut_max)

    def calcular_metricas_competidor(freqs, semana_atual, total_semanas, windsor_cut_max, valor_semana):
        """Calcula a pontuação e o dinheiro recuperado aplicando o corte de Windsor progressivo"""
        if not freqs: 
            return 0.0, 0.0, [], [], [], [], 0
        
        janela = obter_janela_windsor(semana_atual, total_semanas, windsor_cut_max)
        menores_cortadas, maiores_cortadas = [], []
        
        # Aplica o corte apenas se a janela for > 0 e se houver semanas suficientes para cortar
        if janela > 0 and len(freqs) > (2 * janela):
            freqs_ordenadas = sorted(freqs)
            menores_cortadas = freqs_ordenadas[:janela]
            maiores_cortadas = freqs_ordenadas[-janela:]
            freqs_validas = freqs_ordenadas[janela:-janela]
        else:
            freqs_validas = freqs
            
        # 1. Nova Regra: Pontuação baseada na média APÓS o corte
        pontuacao = sum(freqs_validas) / len(freqs_validas) if freqs_validas else 0.0
        
        # 2. Dinheiro Recuperado
        coeficientes = [coefficient_table[min(f, 5)] for f in freqs_validas]
        taxa_media_aproveitamento = sum(coeficientes) / len(coeficientes) if coeficientes else 0.0
        dinheiro_recuperado = taxa_media_aproveitamento * (valor_semana * len(freqs))
        
        return pontuacao, dinheiro_recuperado, freqs_validas, coeficientes, menores_cortadas, maiores_cortadas, janela


    # --- PROCESSAMENTO DO RANKING E AUDITORIA ---
    # --- PROCESSAMENTO DO RANKING E AUDITORIA ---
    current_ranking = []
    previous_ranking = []
    audit_data = [] 
    total_multas_bau = 0.0

    for participant in participantsNames:
        # --- CÁLCULO DA SEMANA ATUAL ---
        treinos_ate_agora = dataCheckins.iloc[0:last_week][participant].tolist()
        
        (pontuacao_atual, dinheiro_recup, freqs_validas, coefs, 
        menores, maiores, janela_atual) = calcular_metricas_competidor(
            treinos_ate_agora, last_week, total_weeks, windsor_cut, valor_por_semana
        )
        
        total_end = df_cumulative.iloc[last_week - 1][participant]
        
        if participant in competidores_reais:
            valor_maximo_possivel = valor_por_semana * last_week
            total_multas_bau += (valor_maximo_possivel - dinheiro_recup)
        
        current_ranking.append({
            "Participant": f"{participant} (Fun)" if participant not in competidores_reais else participant,
            "Pontuação (Média)": pontuacao_atual,
            "Dinheiro Recuperado": dinheiro_recup,
            "Total Geral": int(total_end)
        })
        
        # --- AUDITORIA ATUALIZADA ---
        coefs_formatados = [f"{c*100:.0f}%" for c in coefs]
        audit_data.append({
            "Participante": participant,
            "Janela de Corte Atual": janela_atual,
            "Menores Frequências": str(menores) if menores else "Sem corte",
            "Maiores Frequências": str(maiores) if maiores else "Sem corte",
            "Check-ins Válidos": str(freqs_validas),
            "Cashback Aplicado (%)": str(coefs_formatados),
            "Total Recuperado": dinheiro_recup
        })
        
        # --- CÁLCULO DA SEMANA ANTERIOR (PARA TENDÊNCIA) ---
        if last_week > 1:
            treinos_anteriores = dataCheckins.iloc[0:(last_week - 1)][participant].tolist()
            
            # Chama a função simulando a semana passada para descobrir a pontuação exata
            pontuacao_anterior, _, _, _, _, _, _ = calcular_metricas_competidor(
                treinos_anteriores, (last_week - 1), total_weeks, windsor_cut, valor_por_semana
            )
        else:
            pontuacao_anterior = 0.0
            
        previous_ranking.append({
            "Participant": f"{participant} (Fun)" if participant not in competidores_reais else participant,
            "Pontuação Anterior": pontuacao_anterior
        })

    df_current = pd.DataFrame(current_ranking)
    df_previous = pd.DataFrame(previous_ranking)
    df_audit = pd.DataFrame(audit_data)

    df_current = df_current.sort_values(by="Pontuação (Média)", ascending=False).reset_index(drop=True)
    df_previous = df_previous.sort_values(by="Pontuação Anterior", ascending=False).reset_index(drop=True)

    previous_position = {row['Participant']: idx for idx, row in df_previous.iterrows()}
    trends = []
    for idx, row in df_current.iterrows():
        participant = row['Participant']
        pos_current = idx
        pos_prev = previous_position[participant]
        
        if last_week == initial_week:
            trends.append("➖")
        elif pos_current < pos_prev:
            trends.append("⬆🟩")
        elif pos_current > pos_prev:
            trends.append("⬇🟥")
        else:
            trends.append("➖")

    df_current.insert(0, "Tendência", trends)
    df_current.index = df_current.index + 1
    df_current.index.name = "Posição"


    historico_pontuacao = {p: [] for p in participantsNames}
    for w in range(1, total_weeks + 1):
        for p in participantsNames:
            treinos_ate_w = dataCheckins.iloc[0:w][p].tolist()
            media_w = sum(treinos_ate_w) / len(treinos_ate_w) if treinos_ate_w else 0.0
            historico_pontuacao[p].append(media_w)

    df_pontuacao = pd.DataFrame(historico_pontuacao)
    df_pontuacao.index = range(1, total_weeks + 1)


    # --- CRIANDO AS ABAS ---
    tab1, tab2, tab3 = st.tabs(["Dashboard Principal", "Regras", "Auditoria & Transparência"])

    # ==========================================
    # ABA 1: DASHBOARD PRINCIPAL
    # ==========================================
    with tab1:
        col1, col2 = st.columns([1, 2.5])

        with col1:
            st.subheader("🏆 Ranking Oficial")
            st.dataframe(
                df_current,
                use_container_width=True,
                column_config={
                    "Pontuação (Média)": st.column_config.NumberColumn("Pontuação (Média)", format="%.2f"),
                    "Dinheiro Recuperado": st.column_config.NumberColumn("Dinheiro Recuperado", format="R$ %.2f")
                }
            )
            
            st.subheader("💰 Baú de Prêmios")
            st.metric(label="Prêmio Total Acumulado", value=f"R$ {total_multas_bau:.2f}", delta="Rendimentos a calcular")
            
            st.info("""
            **Divisão do Baú:**
            * 🥇 **1º Lugar:** 80%
            * 🥈 **2º Lugar:** 20%
            """)

        with col2:
            st.subheader("📈 Linha do Tempo: Evolução da Constância")
            
            tipo_grafico = st.radio(
                "Selecione a visualização:",
                options=["Pontuação Média", "Total de Treinos Acumulados"],
                horizontal=True
            )
            
            fig = go.Figure()
            
            if tipo_grafico == "Pontuação Média":
                df_plot = df_pontuacao.iloc[0:last_week]
                y_title = "Pontuação Média"
                max_y = df_plot.max().max()
                tamanho_total_y = (max_y + 1.5) - (-0.2)
                y_range = [-0.2, max_y + 1.5]
            else:
                df_plot = df_cumulative.iloc[0:last_week]
                y_title = "Total de Check-ins Acumulados"
                max_y = int(df_plot.max().max())
                tamanho_total_y = (max_y + 8) - (-2)
                y_range = [-2, max_y + 8]

            tamanho_total_x = (last_week + 2) - (initial_week - 0.2)
            
            # PROPORÇÕES OTIMIZADAS PARA MOBILE (Largura maior, altura ajustada)
            tamanho_img_x = tamanho_total_x * 0.06 
            tamanho_img_y = tamanho_total_y * 0.12

            for participant in participantsNames:
                fig.add_trace(go.Scatter(
                    x=list(range(initial_week, last_week + 1)),
                    y=df_plot[participant],
                    mode='lines',
                    name=f"{participant} (Fun)" if participant not in competidores_reais else participant,
                    line=dict(color=colors.get(participant, "#6c757d"), width=3)
                ))
                
                last_visible_week = last_week
                last_value = df_plot[participant].iloc[-1]
                
                if participant in photos:
                    fonte_imagem = carregar_imagem(photos[participant])
                    
                    if fonte_imagem:
                        fig.add_layout_image(
                            dict(
                                source=fonte_imagem,
                                xref="x",
                                yref="y",
                                x=last_visible_week,
                                y=last_value,
                                sizex=tamanho_img_x, 
                                sizey=tamanho_img_y, 
                                xanchor="left",
                                yanchor="middle",
                                sizing="contain",
                                opacity=1.0
                            )
                        )

            # CONFIGURAÇÕES DE LAYOUT FOCADAS NO CELULAR
            fig.update_layout(
                height=600, # Altura mais amigável para celular
                margin=dict(r=100, l=15, t=10, b=20), # Margens reduzidas nas bordas
                hovermode="x unified",
                
                # Legenda reposicionada para não sobrepor o gráfico em telas estreitas
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.15,
                    xanchor="center",
                    x=0.5,
                    bgcolor="rgba(255, 255, 255, 0.8)", 
                    bordercolor="rgba(0, 0, 0, 0.2)",
                    borderwidth=1
                ),
                
                xaxis=dict(
                    title="", # Remove o título "Semanas" para economizar espaço
                    tickmode="array",
                    tickvals=list(range(initial_week, last_week + 1)),
                    ticktext=[f"Sem {i}" for i in range(initial_week, last_week + 1)],
                    range=[initial_week - 0.2, last_week + 2] 
                ),
                yaxis=dict(
                    title=y_title,
                    range=y_range 
                )
            )

            st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.caption(f"OBS.: As frequências nos extremos para o cálculo da pontuação começam a ser cortadas progresivamente a partir da {total_weeks - windsor_cut*2 + 2}ª semana.")


    # ==========================================
    # ABA 2: REGRAS DO JOGO
    # ==========================================

    with tab2:
        rules = '''
### 🚀 DESAFIO: TCHAU, SEDENTARISMO!

O objetivo aqui não é virar um atleta olímpico da noite para o dia, mas sim encontrar a constância. Segundo o Guia de Atividade Física para a População Brasileira, o segredo da saúde está na rotina (https://bvsms.saude.gov.br/bvs/publicacoes/guia_atividade_fisica_populacao_brasileira.pdf) . Por isso, nosso foco é sair da inércia com equilíbrio.

#### 📅 O JOGO

Início: 25/01/2026

Término: 27/06/2026 (Fechando o primeiro semestre com chave de ouro!)

Duração: 22 semanas.

Investimento: R$ 100,00 (Envia o Pix para: 06366045518).

#### 🏃‍♂️ A META
Praticar exercícios 5 vezes por semana, com duração mínima de 30 minutos cada.

Dica de ouro: Mesmo que você faça um treino super intenso (vigoroso), vamos contabilizá-lo como uma atividade moderada comum. O que importa aqui é o hábito de se mexer!

####💰 COMO FUNCIONA O "CASHBACK" SEMANAL?
Dos seus R$ 100,00 iniciais, uma parte fica disponível para você "resgatar" toda semana, dependendo da sua frequência. Quanto menos você faltar, mais dinheiro volta para o seu bolso!

Valor recuperado semanalmente = (R$ 100 / 22 semanas) x Seu Desempenho.

Tabela de Faltas e Resgate:
| Faltas na Semana |    Quanto você recupera    |
|         0 faltas           | 100% do valor da semana |
|          1 falta            |            60% do valor             |
|          2 faltas          |            40% do valor             |
|          3 faltas          |            20% do valor             |
|          4 faltas          |            10% do valor             |
|          5 faltas          |           R$ 0,00 (Zero)            |

Quem completar os 5 check-ins toda semana recebe seus R$ 100,00 inteirinhos de volta ao final do desafio!

#### 🏆🏆 O BAÚ DE PRÊMIOS 🏆🏆

Todo o valor que não for recuperado pelos participantes (as "multas" por faltas) + os rendimentos do investimento feito pela nossa economista renomada @⁨Beteca Irmã⁩ formará o nosso Grande Baú.

Esse prêmio será dividido entre os campeões de constância:
🥇 1º Lugar: 80% do Baú
🥈 2º Lugar: 20% do Baú

#### 📈 A "Regra do Imprevisto" (Média de Windsor)
Para que uma gripe ou uma semana de trabalho louca não te tirem da disputa, usaremos uma média especial. Ela se chama Média de Windsor (https://pt.wikipedia.org/wiki/Winsoriza%C3%A7%C3%A3o) e terá uma porcentagem de corte de 15 %. Isto é, vamos descartar as suas 3 piores semanas e também as suas 3 melhores. Assim, o que vale é o que você fez na maior parte do tempo. Para subir na média, você precisa ser constante!

#### 📝 OBSERVAÇÕES IMPORTANTES:
O @lhucas atualizará o ranking mensalmente para manter a chama acesa!
Só valem os exercícios que estão na lista oficial na descrição do grupo.
O valor total arrecadado será administrado de forma segura para render até o final do desafio.

#### ✅ EXEMPLO:

Imagine que o desafio dure 10 semanas e você investiu R\$ 100. Isso significa que você tem R\$ 10 para resgatar por semana.

Se você treinar os 5 dias, recebe seus R\$ 10 de volta integralmente. Mas, se tiver 1 falta, você recupera R\$ 6 e os outros R\$ 4 vão direto para o Baú de Prêmios. Se tiver 2 faltas, recupera R\$ 4 e R\$ 6 ficam para o Baú, e assim por diante. No fim, quem for mais constante (pela Média de Windsor) leva toda essa grana acumulada!


⚡🏁 Que comecem os jogos! 🏁⚡
'''
        st.markdown(rules)

    # ==========================================
    # ABA 3: AUDITORIA E TRANSPARÊNCIA
    # ==========================================
    with tab3:
        st.subheader("🔍 Memória de Cálculo (Cashback)")
        st.markdown("Acompanhe exatamente quais semanas foram contabilizadas após a aplicação do corte de Windsor e quais coeficientes de devolução foram gerados.")
        
        st.dataframe(
            df_audit,
            use_container_width=True,
            column_config={
                "Total Recuperado": st.column_config.NumberColumn("Total Recuperado", format="R$ %.2f")
            }
        )
        
        st.divider()
        st.subheader("📊 Base de Dados Bruta (Excel)")
        st.markdown("Tabela original de check-ins registrados.")
        st.dataframe(dataCheckins, use_container_width=True)