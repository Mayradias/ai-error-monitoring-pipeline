# -*- coding: utf-8 -*-
import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="AI Error Monitoring",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# ESTILO CUSTOMIZADO
# ============================================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }

    /* Remove barra branca superior */
    header[data-testid="stHeader"] {
        background-color: #0f1117 !important;
        border-bottom: none !important;
    }

    header[data-testid="stHeader"]::before {
        background-color: #0f1117 !important;
    }

    .main {
        background-color: #0f1117;
    }

    .stApp {
        background-color: #0f1117;
    }

    /* KPI Cards */
    .kpi-card {
        background: linear-gradient(135deg, #1a1d2e 0%, #16192b 100%);
        border: 1px solid #2a2d3e;
        border-radius: 16px;
        padding: 28px 24px;
        text-align: center;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }

    .kpi-card:hover {
        transform: translateY(-2px);
        border-color: #4f6ef7;
    }

    .kpi-label {
        font-family: 'Space Mono', monospace;
        font-size: 11px;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: #6b7280;
        margin-bottom: 12px;
    }

    .kpi-value {
        font-family: 'Space Mono', monospace;
        font-size: 42px;
        font-weight: 700;
        color: #e2e8f0;
        line-height: 1;
        margin-bottom: 8px;
    }

    .kpi-value-accent {
        color: #4f6ef7;
    }

    .kpi-sub {
        font-size: 12px;
        color: #4b5563;
    }

    /* Section headers */
    .section-header {
        font-family: 'Space Mono', monospace;
        font-size: 11px;
        letter-spacing: 3px;
        text-transform: uppercase;
        color: #4f6ef7;
        margin-bottom: 16px;
        padding-bottom: 8px;
        border-bottom: 1px solid #2a2d3e;
    }

    /* Sidebar escura */
    section[data-testid="stSidebar"] {
        background-color: #0a0c14 !important;
        border-right: 1px solid #1e2130;
    }

    /* Títulos da sidebar em branco */
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stMarkdown p {
        color: #e2e8f0 !important;
        font-family: 'DM Sans', sans-serif !important;
    }

    /* Multiselect — fundo escuro, sem vermelho */
    section[data-testid="stSidebar"] .stMultiSelect [data-baseweb="select"] {
        background-color: #1a1d2e !important;
        border-color: #2a2d3e !important;
    }

    section[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] {
        background-color: #2563eb !important;
        color: #e2e8f0 !important;
        border: none !important;
    }

    section[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] span {
        color: #e2e8f0 !important;
    }

    section[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] [data-testid="stIconMaterial"] {
        color: #e2e8f0 !important;
    }

    /* Input do multiselect */
    section[data-testid="stSidebar"] input {
        color: #e2e8f0 !important;
        background-color: transparent !important;
    }

    /* Dropdown do multiselect */
    [data-baseweb="popover"] {
        background-color: #1a1d2e !important;
        border: 1px solid #2a2d3e !important;
    }

    [data-baseweb="menu"] {
        background-color: #1a1d2e !important;
    }

    [data-baseweb="option"] {
        background-color: #1a1d2e !important;
        color: #e2e8f0 !important;
    }

    [data-baseweb="option"]:hover {
        background-color: #2a2d3e !important;
    }

    /* Botão atualizar */
    section[data-testid="stSidebar"] .stButton button {
        background-color: #1a1d2e !important;
        color: #e2e8f0 !important;
        border: 1px solid #2a2d3e !important;
        border-radius: 8px !important;
        width: 100%;
    }

    section[data-testid="stSidebar"] .stButton button:hover {
        border-color: #4f6ef7 !important;
        color: #4f6ef7 !important;
    }

    /* Divider */
    hr {
        border-color: #2a2d3e;
        margin: 32px 0;
    }

    /* Title */
    .dashboard-title {
        font-family: 'Space Mono', monospace;
        font-size: 28px;
        font-weight: 700;
        color: #e2e8f0;
        letter-spacing: -1px;
    }

    .dashboard-subtitle {
        font-size: 13px;
        color: #4b5563;
        margin-top: 4px;
    }

    .accent {
        color: #4f6ef7;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# CONEXÃO COM O BANCO
# ============================================================

@st.cache_resource
def get_connection():
    return psycopg2.connect(
        host="127.0.0.1",
        port=0000,
        dbname="ai_error_monitoring",
        user="postgres",
        password="sua_senha_aqui" 
    )

@st.cache_data(ttl=300)
def carregar_dados():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT
            numero_protocolo,
            secao,
            status,
            data_protocolo,
            motivo_rejeicao,
            categoria,
            tipo_erro
        FROM protocolos
        WHERE data_protocolo IS NOT NULL
        ORDER BY data_protocolo DESC
    """, conn)
    df["data_protocolo"] = pd.to_datetime(df["data_protocolo"])
    df["mes"] = df["data_protocolo"].dt.to_period("M").astype(str)
    df["semana"] = df["data_protocolo"].dt.to_period("W").astype(str)
    return df

# ============================================================
# CARREGAR DADOS
# ============================================================

try:
    df = carregar_dados()
except Exception as e:
    st.error(f"Erro ao conectar ao banco: {e}")
    st.stop()

# ============================================================
# SIDEBAR — FILTROS
# ============================================================

with st.sidebar:
    st.markdown("### 🤖 AI Monitor")
    st.markdown("---")

    st.markdown("**PERÍODO**")
    meses_disponiveis = sorted(df["mes"].unique(), reverse=True)
    meses_selecionados = st.multiselect(
        "Mês",
        options=meses_disponiveis,
        default=meses_disponiveis[:1]
    )

    st.markdown("**SEÇÃO**")
    secoes_disponiveis = sorted(df["secao"].dropna().unique())
    secoes_selecionadas = st.multiselect(
        "Seção",
        options=secoes_disponiveis,
        default=secoes_disponiveis
    )

    st.markdown("---")
    if st.button("🔄 Atualizar dados"):
        st.cache_data.clear()
        st.rerun()

# ============================================================
# APLICAR FILTROS
# ============================================================

df_filtrado = df.copy()

if meses_selecionados:
    df_filtrado = df_filtrado[df_filtrado["mes"].isin(meses_selecionados)]

if secoes_selecionadas:
    df_filtrado = df_filtrado[df_filtrado["secao"].isin(secoes_selecionadas)]

df_aprovados = df_filtrado[df_filtrado["status"] == "APROVADO"]
df_rejeitados = df_filtrado[df_filtrado["status"] == "REJEITADO"]

# ============================================================
# HEADER
# ============================================================

col_title, col_update = st.columns([4, 1])
with col_title:
    st.markdown("""
        <div class="dashboard-title">
            AI <span class="accent">Error</span> Monitoring
        </div>
        <div class="dashboard-subtitle">
            Monitoramento de performance do sistema de extração de documentos societários
        </div>
    """, unsafe_allow_html=True)

with col_update:
    if df_filtrado["data_protocolo"].notna().any():
        ultima = df_filtrado["data_protocolo"].max().strftime("%d/%m/%Y")
        st.markdown(f"<div style='text-align:right; color:#4b5563; font-size:12px; margin-top:16px'>Último registro<br><b style='color:#e2e8f0'>{ultima}</b></div>", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ============================================================
# KPIs
# ============================================================

st.markdown("<div class='section-header'>Visão Geral</div>", unsafe_allow_html=True)

total_protocolos_unicos = df_aprovados["numero_protocolo"].nunique()
total_secoes_aprovadas = len(df_aprovados)
total_rejeitados = df_rejeitados["numero_protocolo"].nunique()
total_geral = df_filtrado["numero_protocolo"].nunique()
taxa_aprovacao = (total_protocolos_unicos / total_geral * 100) if total_geral > 0 else 0

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Protocolos Aprovados</div>
            <div class="kpi-value kpi-value-accent">{total_protocolos_unicos:,}</div>
            <div class="kpi-sub">protocolos únicos</div>
        </div>
    """, unsafe_allow_html=True)

with k2:
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Seções Aprovadas</div>
            <div class="kpi-value">{total_secoes_aprovadas:,}</div>
            <div class="kpi-sub">total de seções</div>
        </div>
    """, unsafe_allow_html=True)

with k3:
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Protocolos Rejeitados</div>
            <div class="kpi-value">{total_rejeitados:,}</div>
            <div class="kpi-sub">protocolos únicos</div>
        </div>
    """, unsafe_allow_html=True)

with k4:
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Taxa de Aprovação</div>
            <div class="kpi-value kpi-value-accent">{taxa_aprovacao:.1f}<span style="font-size:20px">%</span></div>
            <div class="kpi-sub">do total analisado</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================
# GRÁFICOS — LINHA 1
# ============================================================

col_pizza, col_tipo = st.columns([1, 1])

# --- APROVADOS vs REJEITADOS ---
with col_pizza:
    st.markdown("<div class='section-header'>Aprovados vs Rejeitados</div>", unsafe_allow_html=True)

    contagem_status = df_filtrado.groupby("status")["numero_protocolo"].nunique().reset_index()
    contagem_status.columns = ["Status", "Total"]

    fig_pizza = go.Figure(data=[go.Pie(
        labels=contagem_status["Status"],
        values=contagem_status["Total"],
        hole=0.6,
        marker=dict(
            colors=["#4f6ef7", "#ef4444"],
            line=dict(color="#0f1117", width=3)
        ),
        textfont=dict(family="Space Mono", size=11, color="#e2e8f0"),
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>Total: %{value}<br>%{percent}<extra></extra>"
    )])

    fig_pizza.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans", color="#e2e8f0"),
        showlegend=False,
        margin=dict(t=20, b=20, l=20, r=20),
        height=320,
        annotations=[dict(
            text=f"<b>{total_geral}</b><br>total",
            x=0.5, y=0.5,
            font=dict(family="Space Mono", size=16, color="#e2e8f0"),
            showarrow=False
        )]
    )

    st.plotly_chart(fig_pizza, use_container_width=True)

# --- TIPO DE ERRO ---
with col_tipo:
    st.markdown("<div class='section-header'>Tipo de Erro</div>", unsafe_allow_html=True)
    st.markdown("""
        <style>
        .tooltip-wrapper {
            position: relative;
            display: inline-block;
            margin-bottom: 12px;
        }
        .tooltip-wrapper .tooltip-text {
            visibility: hidden;
            opacity: 0;
            background-color: #1a1d2e;
            border: 1px solid #2a2d3e;
            color: #9ca3af;
            font-family: 'DM Sans', sans-serif;
            font-size: 12px;
            line-height: 1.6;
            border-radius: 10px;
            padding: 12px 14px;
            width: 220px;
            position: absolute;
            z-index: 999;
            bottom: 130%;
            left: 0;
            transition: opacity 0.2s ease;
            box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        }
        .tooltip-wrapper:hover .tooltip-text {
            visibility: visible;
            opacity: 1;
        }
        .tooltip-icon {
            cursor: help;
            color: #4b5563;
            font-size: 12px;
            font-family: 'DM Sans', sans-serif;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }
        .tooltip-icon:hover {
            color: #9ca3af;
        }
        </style>

        <div class="tooltip-wrapper">
            <span class="tooltip-icon">
                ⓘ O que é "Não classificado"?
            </span>
            <div class="tooltip-text">
                <b style="color:#e2e8f0">Não classificado</b> representa erros que ocorrem com baixa frequência e ainda não possuem uma categoria definida.<br><br>
                Esses casos são agrupados como <b style="color:#e2e8f0">"Outros"</b> no sistema de classificação e monitorados separadamente para identificar padrões futuros.
            </div>
        </div>
    """, unsafe_allow_html=True)

    df_erros = df_rejeitados[df_rejeitados["tipo_erro"] != "N/A"]
    contagem_tipo = df_erros.groupby("tipo_erro").size().reset_index(name="Total")

    if not contagem_tipo.empty:
        contagem_tipo["Percentual"] = (contagem_tipo["Total"] / contagem_tipo["Total"].sum() * 100).round(1)

        fig_tipo = go.Figure(data=[go.Pie(
            labels=contagem_tipo["tipo_erro"],
            values=contagem_tipo["Total"],
            hole=0.5,
            marker=dict(
                colors=["#f59e0b", "#8b5cf6", "#4f6ef7"],
                line=dict(color="#0f1117", width=3)
            ),
            textfont=dict(family="Space Mono", size=10, color="#e2e8f0"),
            textinfo="percent+label",
            textposition="outside",
            hovertemplate="<b>%{label}</b><br>Total: %{value}<br>%{percent}<extra></extra>"
        )])

        fig_tipo.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="DM Sans", color="#e2e8f0"),
            showlegend=True,
            legend=dict(
                font=dict(family="DM Sans", size=11, color="#9ca3af"),
                bgcolor="rgba(0,0,0,0)",
                orientation="h",
                yanchor="bottom",
                y=-0.3,
                xanchor="center",
                x=0.5
            ),
            margin=dict(t=40, b=80, l=40, r=40),
            height=380,
        )

        st.plotly_chart(fig_tipo, use_container_width=True)
    else:
        st.info("Sem dados de erros para o período selecionado.")

st.markdown("<hr>", unsafe_allow_html=True)

# ============================================================
# GRÁFICO — CATEGORIAS DE ERRO
# ============================================================

st.markdown("<div class='section-header'>Categorias de Erro</div>", unsafe_allow_html=True)

mostrar_outros = st.checkbox("Mostrar 'Outros' (não classificados)", value=True)

df_cat = df_rejeitados[df_rejeitados["categoria"] != "N/A"]

if not mostrar_outros:
    df_cat = df_cat[df_cat["categoria"] != "Outros"]

if not df_cat.empty:
    contagem_cat = df_cat.groupby("categoria").size().reset_index(name="Total")
    contagem_cat = contagem_cat.sort_values("Total", ascending=True)

    fig_cat = go.Figure(go.Bar(
        x=contagem_cat["Total"],
        y=contagem_cat["categoria"],
        orientation="h",
        marker=dict(
            color=contagem_cat["Total"],
            colorscale=[[0, "#1e3a5f"], [0.5, "#2563eb"], [1, "#4f6ef7"]],
            line=dict(color="rgba(0,0,0,0)")
        ),
        text=contagem_cat["Total"],
        textposition="outside",
        textfont=dict(family="Space Mono", size=11, color="#e2e8f0"),
        hovertemplate="<b>%{y}</b><br>Ocorrências: %{x}<extra></extra>"
    ))

    fig_cat.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans", color="#6b7280"),
        xaxis=dict(
            showgrid=True,
            gridcolor="#1e2130",
            zeroline=False,
            color="#4b5563"
        ),
        yaxis=dict(
            showgrid=False,
            color="#9ca3af",
            tickfont=dict(size=11)
        ),
        margin=dict(t=20, b=20, l=20, r=60),
        height=max(300, len(contagem_cat) * 40),
        bargap=0.3
    )

    st.plotly_chart(fig_cat, use_container_width=True)
else:
    st.info("Sem categorias de erro para o período selecionado.")

# ============================================================
# RODAPÉ
# ============================================================

st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("""
    <div style='text-align:center; color:#2a2d3e; font-family: Space Mono; font-size:11px; letter-spacing:2px'>
        AI ERROR MONITORING PIPELINE
    </div>
""", unsafe_allow_html=True)