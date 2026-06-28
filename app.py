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

# --- CONFIGURAÇÃO DE DADOS GLOBAL ---
dataCheckins_real = pd.read_excel('checkin_frequency.xlsx', sheet_name='competitors')
dataCheckins_fun = pd.read_excel('checkin_frequency.xlsx', sheet_name='just_for_fun')

competidores_reais = dataCheckins_real.columns[3:].tolist()
total_weeks = dataCheckins_real.shape[0]

# --- CONTROLES DE TOPO ---
col_slider, col_toggle = st.columns([3, 1])

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
    "Bruna": "img/bruna.jpg"
}
    
colors = {
    "Lhucas": "#0d6efd", "Francis": "#6f42c1", "Félix": "#fd7e14",
    "Ariel": "#20c997", "Elizabeth": "#198754", "Lara": "#e83e8c", "Bruna": "#ffc107"
}

# --- FUNÇÕES DE CÁLCULO ---
def calcular_pontuacao(freqs):
    if not freqs: return 0.0
    return sum(freqs) / len(freqs)

def calcular_dinheiro_recuperado(freqs):
    if not freqs: return 0.0, [], [], [], []
    
    menores_cortadas, maiores_cortadas = [], []
    
    if len(freqs) > (2 * windsor_cut):
        freqs_ordenadas = sorted(freqs)
        menores_cortadas = freqs_ordenadas[:windsor_cut]
        maiores_cortadas = freqs_ordenadas[-windsor_cut:]
        freqs_validas = freqs_ordenadas[windsor_cut:-windsor_cut]
    else:
        freqs_validas = freqs
        
    coeficientes = [coefficient_table[min(f, 5)] for f in freqs_validas]
    taxa_media_aproveitamento = sum(coeficientes) / len(coeficientes)
    dinheiro_recuperado = taxa_media_aproveitamento * (valor_por_semana * len(freqs))
    
    return dinheiro_recuperado, freqs_validas, coeficientes, menores_cortadas, maiores_cortadas


# --- PROCESSAMENTO DO RANKING E AUDITORIA ---
current_ranking = []
previous_ranking = []
audit_data = [] 
total_multas_bau = 0.0

for participant in participantsNames:
    treinos_ate_agora = dataCheckins.iloc[0:last_week][participant].tolist()
    pontuacao_atual = calcular_pontuacao(treinos_ate_agora)
    
    dinheiro_recup, freqs_validas, coefs, menores, maiores = calcular_dinheiro_recuperado(treinos_ate_agora)
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
    
    coefs_formatados = [f"{c*100:.0f}%" for c in coefs]
    audit_data.append({
        "Participante": participant,
        f"{windsor_cut} Menores Frequências": str(menores) if menores else "Sem corte ainda",
        f"{windsor_cut} Maiores Frequências": str(maiores) if maiores else "Sem corte ainda",
        "Check-ins Válidos (Pós-Corte)": str(freqs_validas),
        "Cashback Aplicado (%)": str(coefs_formatados),
        "Total Recuperado": dinheiro_recup
    })
    
    if last_week > 1:
        treinos_anteriores = dataCheckins.iloc[0:(last_week - 1)][participant].tolist()
        pontuacao_anterior = calcular_pontuacao(treinos_anteriores)
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
tab1, tab2 = st.tabs(["🏆 Dashboard Principal", "🕵️‍♂️ Auditoria & Transparência"])

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
    st.caption(f"OBS.: As frequências nos extremos ({windsor_cut} maiores e menores) para o cálculo do dinheiro recuperado são cortadas apenas a partir da {windsor_cut*2 + 1}ª semana.")


# ==========================================
# ABA 2: AUDITORIA E TRANSPARÊNCIA
# ==========================================
with tab2:
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