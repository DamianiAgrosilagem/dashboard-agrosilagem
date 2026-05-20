"""
Dashboard Comercial e Financeiro
AGROSILAGEM SERVICOS AGROPECUARIOS E TRANSPORTES LTDA
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pdfplumber
import re
from pathlib import Path
from datetime import datetime

# ─── Configuração da página ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Agrosilagem — Dashboard Comercial",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Paleta de cores ─────────────────────────────────────────────────────────
VERDE_ESCURO = "#1B5E20"
VERDE_MEDIO  = "#2E7D32"
VERDE_CLARO  = "#4CAF50"
AMARELO      = "#F9A825"
LARANJA      = "#E65100"
AZUL         = "#0D47A1"
CINZA_BG     = "#F5F5F5"
BRANCO       = "#FFFFFF"

PALETTE = [
    "#2E7D32", "#1565C0", "#E65100", "#6A1B9A",
    "#00838F", "#AD1457", "#F57F17", "#4E342E",
    "#37474F", "#558B2F", "#0277BD", "#D84315",
]

# ─── CSS customizado + responsivo mobile ─────────────────────────────────────
st.markdown("""
<style>
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #1B5E20; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stMultiSelect label,
    [data-testid="stSidebar"] .stSlider label { color: #FFFFFF !important; }

    /* KPI Cards */
    .kpi-card {
        background: linear-gradient(135deg, #2E7D32, #1B5E20);
        border-radius: 12px;
        padding: 20px 24px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        margin-bottom: 8px;
    }
    .kpi-card .kpi-value { font-size: 1.8rem; font-weight: 700; margin: 8px 0; }
    .kpi-card .kpi-label { font-size: 0.78rem; text-transform: uppercase; letter-spacing: 1px; opacity: 0.85; }
    .kpi-card .kpi-delta { font-size: 0.82rem; margin-top: 4px; opacity: 0.9; }

    .kpi-card.azul   { background: linear-gradient(135deg, #1565C0, #0D47A1); }
    .kpi-card.laranja{ background: linear-gradient(135deg, #E65100, #BF360C); }
    .kpi-card.roxo   { background: linear-gradient(135deg, #6A1B9A, #4A148C); }
    .kpi-card.teal   { background: linear-gradient(135deg, #00838F, #006064); }

    /* Section titles */
    .section-title {
        font-size: 1.05rem; font-weight: 600;
        color: #1B5E20; border-left: 4px solid #4CAF50;
        padding-left: 10px; margin: 18px 0 12px 0;
    }

    /* Insight box */
    .insight-box {
        background: #E8F5E9; border-left: 4px solid #4CAF50;
        border-radius: 6px; padding: 12px 16px;
        margin: 6px 0; font-size: 0.88rem; color: #1B5E20;
    }
    .insight-box.alerta {
        background: #FFF3E0; border-left-color: #E65100; color: #BF360C;
    }

    /* Header */
    .main-header {
        background: linear-gradient(90deg, #1B5E20, #2E7D32);
        padding: 16px 24px; border-radius: 10px;
        color: white; margin-bottom: 20px;
        display: flex; align-items: center; gap: 16px;
    }
    .main-header h1 { margin: 0; font-size: 1.4rem; }
    .main-header p  { margin: 2px 0; font-size: 0.82rem; opacity: 0.85; }

    /* Tabs */
    .stTabs [data-baseweb="tab"] { font-weight: 600; color: #2E7D32; }

    /* Scrollable table */
    .dataframe-container { overflow-x: auto; }

    /* Remove default margins */
    .block-container { padding-top: 1rem; }

    /* ── RESPONSIVO MOBILE ── */
    @media (max-width: 768px) {
        /* Empilhar colunas */
        [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
        }
        /* KPI menor */
        .kpi-card .kpi-value { font-size: 1.3rem; }
        .kpi-card { padding: 14px 12px; }
        /* Header compacto */
        .main-header h1 { font-size: 1.1rem; }
        .main-header p  { font-size: 0.72rem; }
        /* Tabs scroll horizontal */
        .stTabs [data-testid="stHorizontalBlock"] { overflow-x: auto; }
        /* Padding menor */
        .block-container { padding: 0.5rem 0.5rem 2rem !important; }
        /* Sidebar fecha por padrão no mobile — já é padrão do Streamlit */
    }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# FUNÇÕES DE EXTRAÇÃO DE PDF
# ═══════════════════════════════════════════════════════════════════

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
PDF_DIR  = BASE_DIR.parent  # pasta DOWLOAD

VENDAS_FILE = DATA_DIR / "vendas.csv.gz"


def parse_br_number(s):
    if not s:
        return 0.0
    s = str(s).strip().replace('\n', '').replace(' ', '').replace('.', '').replace(',', '.')
    try:
        return float(s)
    except:
        return 0.0


def categorize_produto(produto):
    p = str(produto).upper()
    if any(k in p for k in ['CORTE DE SILAGEM', 'CLAAS', 'FR 500', 'FR BIG', 'KRONE']):
        return 'Corte de Silagem'
    if 'FRETE TERCEIROS' in p:
        return 'Frete Terceiros'
    if any(k in p for k in ['M.BENZ', 'FORD CARGO', 'VOLVO', 'SCANIA']):
        return 'Caminhões'
    if 'TRATOR' in p:
        return 'Tratores'
    if 'DIESEL' in p:
        return 'Ajuste de Diesel'
    if 'KM' in p:
        return 'KM Excedente'
    return 'Outros'


def extract_safra(detalhes):
    if not detalhes:
        return 'Outros Serviços'
    d = str(detalhes).upper()
    mapping = [
        (['INVERNO', '2023'], 'Safra Inverno 2023'),
        (['INVERNO', '2024'], 'Safra Inverno 2024'),
        (['INVERNO', '2025'], 'Safra Inverno 2025'),
        (['INVERNO', '2026'], 'Safra Inverno 2026'),
        (['VER', '2025'],     'Safra Verão 2025'),
        (['VER', '2026'],     'Safra Verão 2026'),
        (['SAFRINHA', '2024'], 'Safrinha 2024'),
        (['SAFRINHA', '2025'], 'Safrinha 2025'),
        (['SAFRINHA', '2026'], 'Safrinha 2026'),
    ]
    for keys, label in mapping:
        if all(k in d for k in keys):
            return label
    for yr in ['2023', '2024', '2025', '2026']:
        if yr in d:
            return f'Safra {yr}'
    return 'Outros Serviços'


@st.cache_data(show_spinner=False)
def extract_pdf1(path):
    rows = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                for row in table:
                    if not row or len(row) < 8:
                        continue
                    r0 = str(row[0]).strip().replace('\n', '') if row[0] else ''
                    if not r0 or not re.match(r'^\d+$', r0) or len(r0) > 5:
                        continue
                    rows.append(row[:8])
    return rows


@st.cache_data(show_spinner=False)
def extract_pdf2(path):
    rows = []
    current_venda, current_cliente = None, None
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                for row in table:
                    if not row or len(row) < 8:
                        continue
                    r0 = str(row[0]).replace('\n', ' ').strip() if row[0] else ''
                    r1 = str(row[1]).replace('\n', ' ').strip() if row[1] else ''
                    r2 = str(row[2]).replace('\n', ' ').strip() if row[2] else ''
                    r3 = str(row[3]).replace('\n', ' ').strip() if row[3] else ''
                    r4, r5, r6, r7 = row[4], row[5], row[6], row[7]

                    if 'Número' in r0 or 'Total geral' in r0:
                        continue
                    if 'Total' in r0 or 'Total' in r1:
                        continue

                    if re.match(r'^\d+$', r0):
                        current_venda = int(r0)
                        current_cliente = r1
                        data = r2 if re.match(r'\d{2}/\d{2}/\d{4}', r2) else ''
                        detalhes = r3
                    elif current_venda:
                        data = r2 if re.match(r'\d{2}/\d{2}/\d{4}', r2) else ''
                        detalhes = r3 if r3 else (r0 if r0 else r1)
                    else:
                        continue

                    vb = parse_br_number(r5)
                    vl = parse_br_number(r7)
                    qtd = parse_br_number(r4)
                    if vb > 0 and detalhes:
                        rows.append({
                            'num_venda': current_venda,
                            'cliente': current_cliente,
                            'data_venda': data,
                            'detalhes': detalhes,
                            'quantidade': qtd,
                            'valor_bruto': vb,
                            'valor_unitario': parse_br_number(r6),
                            'valor_liquido': vl,
                        })
    return rows


@st.cache_data(show_spinner=False)
def build_dataset():
    """Carrega CSV comprimido; se não existir, extrai dos PDFs."""
    if VENDAS_FILE.exists():
        df = pd.read_csv(VENDAS_FILE, compression='gzip',
                         parse_dates=['data_venda'])
        df['is_silagem'] = df['is_silagem'].astype(bool)
        df['hectares']   = df['hectares'].fillna(0)
        return df

    # Extração dos PDFs
    pdf1 = PDF_DIR / "Relatório de Vendas por Safra.pdf"
    pdf2 = PDF_DIR / "RESUMO DE VENDAS.pdf"

    if not pdf1.exists() or not pdf2.exists():
        st.error("PDFs não encontrados. Coloque-os em: " + str(PDF_DIR))
        st.stop()

    with st.spinner("Extraindo dados dos PDFs (primeira execução — aguarde ~2 min)..."):
        rows1 = extract_pdf1(str(pdf1))
        rows2 = extract_pdf2(str(pdf2))

    df1_data = []
    for row in rows1:
        num = str(row[0]).strip()
        if not re.match(r'^\d+$', num):
            continue
        produto = str(row[4]).replace('\n', ' ').strip()
        safra   = str(row[5]).replace('\n', ' ').strip()
        df1_data.append({
            'num_venda':  int(num),
            'data_venda': str(row[1]).replace('\n', ' ').strip(),
            'cliente':    str(row[2]).replace('\n', ' ').strip(),
            'cidade':     str(row[3]).replace('\n', ' ').strip(),
            'produto':    produto,
            'safra_raw':  safra,
            'quantidade': parse_br_number(row[6]),
            'valor_bruto': parse_br_number(row[7]),
            'categoria':  categorize_produto(produto),
            'safra':      extract_safra(safra),
            'is_silagem': any(k in produto.upper() for k in
                              ['CORTE DE SILAGEM', 'CLAAS', 'FR 500', 'FR BIG', 'KRONE']),
        })

    df = pd.DataFrame(df1_data)
    df['data_venda'] = pd.to_datetime(df['data_venda'], format='%d/%m/%Y', errors='coerce')
    df['cidade'] = df['cidade'].str.title().str.strip()

    df2 = pd.DataFrame(rows2)
    vl_por_venda = df2.groupby('num_venda')['valor_liquido'].sum().reset_index()
    vl_por_venda.columns = ['num_venda', 'valor_liquido_total_venda']
    df = df.merge(vl_por_venda, on='num_venda', how='left')
    vb_por_venda = df.groupby('num_venda')['valor_bruto'].transform('sum')
    df['valor_liquido'] = (
        df['valor_bruto'] / vb_por_venda.replace(0, 1)
        * df['valor_liquido_total_venda'].fillna(df['valor_bruto'])
    )
    df['hectares'] = df.apply(lambda r: r['quantidade'] if r['is_silagem'] else 0.0, axis=1)

    DATA_DIR.mkdir(exist_ok=True)
    df.to_parquet(VENDAS_FILE, index=False)
    return df


# ═══════════════════════════════════════════════════════════════════
# HELPERS DE FORMATAÇÃO
# ═══════════════════════════════════════════════════════════════════

def fmt_brl(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def fmt_num(v, decimals=0):
    fmt = f"{v:,.{decimals}f}"
    return fmt.replace(",", "X").replace(".", ",").replace("X", ".")

def kpi(label, value, cls="", delta=""):
    delta_html = f'<div class="kpi-delta">{delta}</div>' if delta else ""
    return f"""
<div class="kpi-card {cls}">
    <div class="kpi-label">{label}</div>
    <div class="kpi-value">{value}</div>
    {delta_html}
</div>
"""

def layout_mobile(fig, height=380, margin_b=60, font_size=13):
    """Aplica configurações de legibilidade mobile em qualquer figura Plotly."""
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=36, b=margin_b),
        font=dict(size=font_size, family="Arial, sans-serif"),
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend=dict(
            orientation="h", y=-0.22, x=0,
            font=dict(size=11),
        ),
    )
    fig.update_xaxes(tickfont=dict(size=11), title_font=dict(size=12))
    fig.update_yaxes(tickfont=dict(size=11), title_font=dict(size=12))
    return fig


# ═══════════════════════════════════════════════════════════════════
# CARREGAMENTO DOS DADOS
# ═══════════════════════════════════════════════════════════════════

df_raw = build_dataset()
df_raw['ano_mes'] = df_raw['data_venda'].dt.to_period('M').astype(str)
df_raw['ano']     = df_raw['data_venda'].dt.year
df_raw['mes']     = df_raw['data_venda'].dt.month


# ═══════════════════════════════════════════════════════════════════
# SIDEBAR — FILTROS
# ═══════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## 🌾 Agrosilagem")
    st.markdown("### Filtros")

    # Datas
    min_date = df_raw['data_venda'].min().date()
    max_date = df_raw['data_venda'].max().date()
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        dt_inicio = st.date_input("De", value=min_date, min_value=min_date, max_value=max_date,
                                  format="DD/MM/YYYY")
    with col_d2:
        dt_fim    = st.date_input("Até", value=max_date, min_value=min_date, max_value=max_date,
                                  format="DD/MM/YYYY")

    # Safra
    safras_disp = sorted(df_raw['safra'].dropna().unique())
    safra_sel = st.multiselect("Safra", safras_disp, default=[])

    # Categoria de produto
    cats_disp = sorted(df_raw['categoria'].dropna().unique())
    cat_sel = st.multiselect("Categoria", cats_disp, default=[])

    # Cidade
    cidades_disp = sorted(df_raw['cidade'].dropna().unique())
    cidade_sel = st.multiselect("Cidade", cidades_disp, default=[])

    # Cliente (top 50 por faturamento para não sobrecarregar o select)
    top_clientes = (
        df_raw.groupby('cliente')['valor_bruto'].sum()
        .sort_values(ascending=False).head(50).index.tolist()
    )
    clientes_disp = sorted(df_raw['cliente'].dropna().unique())
    cliente_sel = st.multiselect("Cliente", clientes_disp, default=[])

    # Faixa de hectares
    max_ha = int(df_raw[df_raw['is_silagem']]['quantidade'].max())
    ha_range = st.slider("Faixa de Hectares", 0, max_ha, (0, max_ha))

    st.markdown("---")
    if st.button("🔄 Atualizar Dados"):
        if VENDAS_FILE.exists():
            VENDAS_FILE.unlink()
        st.cache_data.clear()
        st.rerun()


# ═══════════════════════════════════════════════════════════════════
# APLICAR FILTROS
# ═══════════════════════════════════════════════════════════════════

df = df_raw.copy()
df = df[df['data_venda'].dt.date.between(dt_inicio, dt_fim)]
if safra_sel:
    df = df[df['safra'].isin(safra_sel)]
if cat_sel:
    df = df[df['categoria'].isin(cat_sel)]
if cidade_sel:
    df = df[df['cidade'].isin(cidade_sel)]
if cliente_sel:
    df = df[df['cliente'].isin(cliente_sel)]
# Hectares filter applies only to silagem rows
mask_ha = (
    (~df['is_silagem']) |
    (df['quantidade'].between(ha_range[0], ha_range[1]))
)
df = df[mask_ha]


# ═══════════════════════════════════════════════════════════════════
# MÉTRICAS CALCULADAS
# ═══════════════════════════════════════════════════════════════════

fat_total     = df['valor_bruto'].sum()
liq_total     = df['valor_liquido'].sum()
total_clientes = df['cliente'].nunique()
total_ha      = df['hectares'].sum()
rec_ha        = fat_total / total_ha if total_ha > 0 else 0

# Ticket médio: valor total por venda / hectares totais daquela venda
vendas_agg = df.groupby('num_venda').agg(
    fat_venda=('valor_bruto', 'sum'),
    ha_venda=('hectares', 'sum'),
).reset_index()
vendas_com_ha = vendas_agg[vendas_agg['ha_venda'] > 0]
ticket_medio = (
    (vendas_com_ha['fat_venda'] / vendas_com_ha['ha_venda']).mean()
    if len(vendas_com_ha) > 0 else 0
)

num_vendas    = df['num_venda'].nunique()


# ═══════════════════════════════════════════════════════════════════
# CABEÇALHO
# ═══════════════════════════════════════════════════════════════════

st.markdown("""
<div class="main-header">
    <div style="font-size:2.5rem">🌾</div>
    <div>
        <h1>Dashboard Comercial & Financeiro</h1>
        <p>AGROSILAGEM SERVICOS AGROPECUARIOS E TRANSPORTES LTDA &nbsp;|&nbsp; Análise de vendas e safras</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Período exibido
periodo_str = f"{dt_inicio.strftime('%d/%m/%Y')} — {dt_fim.strftime('%d/%m/%Y')}"
registros_str = f"{len(df):,} registros | {num_vendas:,} vendas realizadas"
st.caption(f"📅 Período: **{periodo_str}** &nbsp;|&nbsp; {registros_str}")


# ═══════════════════════════════════════════════════════════════════
# KPI CARDS
# ═══════════════════════════════════════════════════════════════════

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.markdown(kpi("Faturamento Bruto", fmt_brl(fat_total)), unsafe_allow_html=True)
with c2:
    st.markdown(kpi("Receita Líquida", fmt_brl(liq_total), cls="azul"), unsafe_allow_html=True)
with c3:
    st.markdown(kpi("Ticket Médio / ha", fmt_brl(ticket_medio), cls="laranja",
                    delta=f"{len(vendas_com_ha)} vendas c/ ha"), unsafe_allow_html=True)
with c4:
    st.markdown(kpi("Total de Hectares", fmt_num(total_ha, 1), cls="roxo",
                    delta=fmt_brl(rec_ha) + "/ha"), unsafe_allow_html=True)
with c5:
    st.markdown(kpi("Clientes Ativos", fmt_num(total_clientes), cls="teal",
                    delta=f"{num_vendas} vendas"), unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# ABAS
# ═══════════════════════════════════════════════════════════════════

tab_visao, tab_clientes, tab_produtos, tab_geo, tab_temporal, tab_safras, tab_dados, tab_insights = st.tabs([
    "📊 Visão Geral",
    "👥 Clientes",
    "🚜 Produtos",
    "📍 Cidades",
    "📈 Evolução Mensal",
    "🌱 Safras",
    "📋 Dados",
    "💡 Insights",
])


# ───────────────────────────────────────────────────────────────────
# ABA 1 — VISÃO GERAL
# ───────────────────────────────────────────────────────────────────

with tab_visao:
    col_l, col_r = st.columns([1, 1])

    with col_l:
        st.markdown('<div class="section-title">Faturamento por Categoria de Produto</div>', unsafe_allow_html=True)
        cat_df = (
            df.groupby('categoria')['valor_bruto'].sum()
            .sort_values(ascending=True).reset_index()
        )
        fig_cat = px.bar(
            cat_df, x='valor_bruto', y='categoria',
            orientation='h',
            color='categoria', color_discrete_sequence=PALETTE,
            text=cat_df['valor_bruto'].apply(lambda v: fmt_brl(v)),
        )
        fig_cat.update_traces(textposition='outside', textfont_size=11)
        layout_mobile(fig_cat, height=340, margin_b=10)
        fig_cat.update_layout(showlegend=False,
            xaxis=dict(showticklabels=False, showgrid=False), xaxis_title="", yaxis_title="")
        st.plotly_chart(fig_cat, use_container_width=True)

    with col_r:
        st.markdown('<div class="section-title">Distribuição do Faturamento por Categoria</div>', unsafe_allow_html=True)
        fig_pie = px.pie(
            cat_df, values='valor_bruto', names='categoria',
            color_discrete_sequence=PALETTE, hole=0.45,
        )
        fig_pie.update_traces(
            textposition='inside', textinfo='label+percent',
            textfont_size=12, insidetextorientation='radial',
        )
        layout_mobile(fig_pie, height=340, margin_b=10)
        fig_pie.update_layout(showlegend=False)
        st.plotly_chart(fig_pie, use_container_width=True)

    # Faturamento bruto vs líquido por categoria
    st.markdown('<div class="section-title">Bruto vs Líquido por Categoria</div>', unsafe_allow_html=True)
    bvsl = (
        df.groupby('categoria')
        .agg(bruto=('valor_bruto', 'sum'), liquido=('valor_liquido', 'sum'))
        .sort_values('bruto', ascending=False).reset_index()
    )
    fig_bvsl = go.Figure()
    fig_bvsl.add_trace(go.Bar(
        x=bvsl['categoria'], y=bvsl['bruto'],
        name='Bruto', marker_color=VERDE_CLARO,
        text=bvsl['bruto'].apply(fmt_brl), textposition='outside', textfont_size=11,
    ))
    fig_bvsl.add_trace(go.Bar(
        x=bvsl['categoria'], y=bvsl['liquido'],
        name='Líquido', marker_color=AZUL,
        text=bvsl['liquido'].apply(fmt_brl), textposition='outside', textfont_size=11,
    ))
    layout_mobile(fig_bvsl, height=360, margin_b=60)
    fig_bvsl.update_layout(barmode='group', xaxis_title="", yaxis_title="R$")
    st.plotly_chart(fig_bvsl, use_container_width=True)


# ───────────────────────────────────────────────────────────────────
# ABA 2 — CLIENTES
# ───────────────────────────────────────────────────────────────────

with tab_clientes:
    n_top = st.slider("Mostrar top N clientes", 5, 50, 20, key="top_cli")

    cli_df = (
        df.groupby('cliente').agg(
            faturamento=('valor_bruto', 'sum'),
            liquido=('valor_liquido', 'sum'),
            hectares=('hectares', 'sum'),
            num_vendas=('num_venda', 'nunique'),
            cidade=('cidade', lambda x: x.mode()[0] if len(x) > 0 else ''),
        ).sort_values('faturamento', ascending=False).reset_index()
    )
    cli_df['ticket_medio_ha'] = cli_df.apply(
        lambda r: r['faturamento'] / r['hectares'] if r['hectares'] > 0 else 0, axis=1
    )
    cli_df['rank'] = range(1, len(cli_df) + 1)

    col_l, col_r = st.columns([2, 1])

    with col_l:
        st.markdown('<div class="section-title">Ranking de Faturamento por Cliente</div>', unsafe_allow_html=True)
        top_cli = cli_df.head(n_top)
        fig_cli = px.bar(
            top_cli.sort_values('faturamento'),
            x='faturamento', y='cliente',
            orientation='h', color='faturamento',
            color_continuous_scale=['#A5D6A7', '#1B5E20'],
            text=top_cli.sort_values('faturamento')['faturamento'].apply(fmt_brl),
        )
        fig_cli.update_traces(textposition='outside', textfont_size=11)
        layout_mobile(fig_cli, height=max(380, n_top * 24), margin_b=10)
        fig_cli.update_layout(showlegend=False, coloraxis_showscale=False,
            xaxis=dict(showticklabels=False, showgrid=False), yaxis_title="", xaxis_title="")
        st.plotly_chart(fig_cli, use_container_width=True)

    with col_r:
        st.markdown('<div class="section-title">Ticket Médio / ha (Top 15)</div>', unsafe_allow_html=True)
        tm_df = cli_df[cli_df['hectares'] > 0].head(15).sort_values('ticket_medio_ha')
        fig_tm = px.bar(
            tm_df, x='ticket_medio_ha', y='cliente',
            orientation='h', color='ticket_medio_ha',
            color_continuous_scale=['#B3E5FC', '#01579B'],
            text=tm_df['ticket_medio_ha'].apply(lambda v: fmt_brl(v)),
        )
        fig_tm.update_traces(textposition='outside', textfont_size=11)
        layout_mobile(fig_tm, height=400, margin_b=10)
        fig_tm.update_layout(showlegend=False, coloraxis_showscale=False,
            xaxis=dict(showticklabels=False, showgrid=False), yaxis_title="", xaxis_title="")
        st.plotly_chart(fig_tm, use_container_width=True)

    # Tabela resumo de clientes
    st.markdown('<div class="section-title">Tabela de Clientes</div>', unsafe_allow_html=True)
    cli_show = cli_df.head(n_top).copy()
    cli_show['faturamento']     = cli_show['faturamento'].apply(fmt_brl)
    cli_show['liquido']         = cli_show['liquido'].apply(fmt_brl)
    cli_show['hectares']        = cli_show['hectares'].apply(lambda v: fmt_num(v, 1))
    cli_show['ticket_medio_ha'] = cli_show['ticket_medio_ha'].apply(fmt_brl)
    cli_show = cli_show.rename(columns={
        'rank': '#', 'cliente': 'Cliente', 'cidade': 'Cidade',
        'faturamento': 'Faturamento', 'liquido': 'Líquido',
        'hectares': 'Hectares', 'num_vendas': 'Nº Vendas',
        'ticket_medio_ha': 'Ticket/ha',
    })
    st.dataframe(cli_show[['#', 'Cliente', 'Cidade', 'Faturamento', 'Líquido', 'Hectares', 'Ticket/ha', 'Nº Vendas']],
                 use_container_width=True, hide_index=True)

    # Comparativo hectares x faturamento
    st.markdown('<div class="section-title">Comparativo Hectares × Faturamento (Bubble)</div>', unsafe_allow_html=True)
    bubble_df = cli_df[cli_df['hectares'] > 0].head(40)
    fig_bubble = px.scatter(
        bubble_df,
        x='hectares', y='faturamento',
        size='faturamento', color='ticket_medio_ha',
        hover_name='cliente',
        hover_data={'hectares': ':.1f', 'faturamento': ':,.2f', 'ticket_medio_ha': ':,.2f'},
        color_continuous_scale='Greens',
        size_max=60, labels={'hectares': 'Hectares', 'faturamento': 'Faturamento (R$)'},
        text='cliente',
    )
    fig_bubble.update_traces(textposition='top center', textfont_size=10)
    layout_mobile(fig_bubble, height=460, margin_b=60)
    fig_bubble.update_layout(coloraxis_colorbar_title="Ticket/ha")
    st.plotly_chart(fig_bubble, use_container_width=True)


# ───────────────────────────────────────────────────────────────────
# ABA 3 — PRODUTOS
# ───────────────────────────────────────────────────────────────────

with tab_produtos:
    col_l, col_r = st.columns(2)

    prod_df = (
        df.groupby('produto').agg(
            faturamento=('valor_bruto', 'sum'),
            quantidade=('quantidade', 'sum'),
            ocorrencias=('num_venda', 'count'),
        ).sort_values('faturamento', ascending=False).reset_index()
    )

    with col_l:
        st.markdown('<div class="section-title">Top 15 Produtos por Faturamento</div>', unsafe_allow_html=True)
        top15 = prod_df.head(15).sort_values('faturamento')
        fig_prod = px.bar(
            top15, x='faturamento', y='produto',
            orientation='h', color='faturamento',
            color_continuous_scale=['#C8E6C9', '#1B5E20'],
            text=top15['faturamento'].apply(fmt_brl),
        )
        fig_prod.update_traces(textposition='outside', textfont_size=11)
        layout_mobile(fig_prod, height=440, margin_b=10)
        fig_prod.update_layout(showlegend=False, coloraxis_showscale=False,
            xaxis=dict(showticklabels=False, showgrid=False), yaxis_title="", xaxis_title="")
        st.plotly_chart(fig_prod, use_container_width=True)

    with col_r:
        st.markdown('<div class="section-title">Top 15 Produtos por Volume</div>', unsafe_allow_html=True)
        top15q = prod_df.sort_values('quantidade', ascending=False).head(15).sort_values('quantidade')
        fig_prodq = px.bar(
            top15q, x='quantidade', y='produto',
            orientation='h', color='quantidade',
            color_continuous_scale=['#B3E5FC', '#01579B'],
            text=top15q['quantidade'].apply(lambda v: fmt_num(v, 1)),
        )
        fig_prodq.update_traces(textposition='outside', textfont_size=11)
        layout_mobile(fig_prodq, height=440, margin_b=10)
        fig_prodq.update_layout(showlegend=False, coloraxis_showscale=False,
            xaxis=dict(showticklabels=False, showgrid=False), yaxis_title="", xaxis_title="")
        st.plotly_chart(fig_prodq, use_container_width=True)

    # Silagem detail
    st.markdown('<div class="section-title">Detalhe — Corte de Silagem (hectares cortados por equipamento)</div>', unsafe_allow_html=True)
    sil_df = (
        df[df['is_silagem']].groupby('produto').agg(
            hectares=('quantidade', 'sum'),
            faturamento=('valor_bruto', 'sum'),
            ocorrencias=('num_venda', 'count'),
        ).sort_values('hectares', ascending=False).reset_index()
    )
    sil_df['receita_ha'] = sil_df['faturamento'] / sil_df['hectares']

    fig_sil = make_subplots(rows=1, cols=2,
                            subplot_titles=("Hectares cortados", "Receita por Hectare"))
    fig_sil.add_trace(
        go.Bar(x=sil_df['produto'], y=sil_df['hectares'],
               marker_color=VERDE_CLARO,
               text=sil_df['hectares'].apply(lambda v: fmt_num(v, 1)),
               textposition='outside', name='ha'),
        row=1, col=1
    )
    fig_sil.add_trace(
        go.Bar(x=sil_df['produto'], y=sil_df['receita_ha'],
               marker_color=AMARELO,
               text=sil_df['receita_ha'].apply(fmt_brl),
               textposition='outside', name='R$/ha'),
        row=1, col=2
    )
    layout_mobile(fig_sil, height=420, margin_b=100)
    fig_sil.update_layout(showlegend=False)
    fig_sil.update_xaxes(tickangle=35, tickfont=dict(size=10))
    st.plotly_chart(fig_sil, use_container_width=True)


# ───────────────────────────────────────────────────────────────────
# ABA 4 — CIDADES
# ───────────────────────────────────────────────────────────────────

with tab_geo:
    n_cid = st.slider("Top N cidades", 5, 40, 20, key="top_cid")

    cid_df = (
        df.groupby('cidade').agg(
            faturamento=('valor_bruto', 'sum'),
            clientes=('cliente', 'nunique'),
            hectares=('hectares', 'sum'),
        ).sort_values('faturamento', ascending=False).reset_index()
    )

    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown('<div class="section-title">Faturamento por Cidade</div>', unsafe_allow_html=True)
        top_cid = cid_df.head(n_cid).sort_values('faturamento')
        fig_cid = px.bar(
            top_cid, x='faturamento', y='cidade',
            orientation='h', color='faturamento',
            color_continuous_scale=['#A5D6A7', '#1B5E20'],
            text=top_cid['faturamento'].apply(fmt_brl),
        )
        fig_cid.update_traces(textposition='outside', textfont_size=11)
        layout_mobile(fig_cid, height=max(380, n_cid * 24), margin_b=10)
        fig_cid.update_layout(showlegend=False, coloraxis_showscale=False,
            xaxis=dict(showticklabels=False, showgrid=False), yaxis_title="", xaxis_title="")
        st.plotly_chart(fig_cid, use_container_width=True)

    with col_r:
        st.markdown('<div class="section-title">Clientes por Cidade (Top 20)</div>', unsafe_allow_html=True)
        top_cid_c = cid_df.sort_values('clientes', ascending=False).head(20).sort_values('clientes')
        fig_cid_c = px.bar(
            top_cid_c, x='clientes', y='cidade',
            orientation='h', color='clientes',
            color_continuous_scale=['#B3E5FC', '#01579B'],
            text=top_cid_c['clientes'],
        )
        fig_cid_c.update_traces(textposition='outside', textfont_size=11)
        layout_mobile(fig_cid_c, height=500, margin_b=10)
        fig_cid_c.update_layout(showlegend=False, coloraxis_showscale=False,
            xaxis=dict(showticklabels=False, showgrid=False), yaxis_title="", xaxis_title="")
        st.plotly_chart(fig_cid_c, use_container_width=True)

    # Tabela cidades
    st.markdown('<div class="section-title">Tabela de Cidades</div>', unsafe_allow_html=True)
    cid_show = cid_df.head(n_cid).copy()
    cid_show['rank'] = range(1, len(cid_show) + 1)
    cid_show['faturamento_fmt'] = cid_show['faturamento'].apply(fmt_brl)
    cid_show['hectares_fmt']    = cid_show['hectares'].apply(lambda v: fmt_num(v, 1))
    cid_show['receita_ha'] = cid_show.apply(
        lambda r: fmt_brl(r['faturamento'] / r['hectares']) if r['hectares'] > 0 else '-', axis=1
    )
    st.dataframe(
        cid_show[['rank', 'cidade', 'faturamento_fmt', 'clientes', 'hectares_fmt', 'receita_ha']]
        .rename(columns={'rank': '#', 'cidade': 'Cidade', 'faturamento_fmt': 'Faturamento',
                         'clientes': 'Clientes', 'hectares_fmt': 'Hectares', 'receita_ha': 'Receita/ha'}),
        use_container_width=True, hide_index=True,
    )


# ───────────────────────────────────────────────────────────────────
# ABA 5 — EVOLUÇÃO MENSAL
# ───────────────────────────────────────────────────────────────────

with tab_temporal:
    mensal = (
        df.groupby('ano_mes').agg(
            faturamento=('valor_bruto', 'sum'),
            liquido=('valor_liquido', 'sum'),
            hectares=('hectares', 'sum'),
            vendas=('num_venda', 'nunique'),
            clientes=('cliente', 'nunique'),
        ).reset_index().sort_values('ano_mes')
    )
    mensal['ticket_ha'] = mensal.apply(
        lambda r: r['faturamento'] / r['hectares'] if r['hectares'] > 0 else None, axis=1
    )

    st.markdown('<div class="section-title">Evolução Mensal do Faturamento</div>', unsafe_allow_html=True)
    fig_mensal = go.Figure()
    fig_mensal.add_trace(go.Bar(
        x=mensal['ano_mes'], y=mensal['faturamento'],
        name='Faturamento Bruto', marker_color=VERDE_CLARO, opacity=0.85,
    ))
    fig_mensal.add_trace(go.Scatter(
        x=mensal['ano_mes'], y=mensal['liquido'],
        name='Receita Líquida', line=dict(color=AZUL, width=3),
        mode='lines+markers', marker=dict(size=7),
    ))
    layout_mobile(fig_mensal, height=420, margin_b=80)
    fig_mensal.update_layout(barmode='overlay', xaxis_title="Mês/Ano", yaxis_title="R$")
    fig_mensal.update_xaxes(tickangle=45, tickfont=dict(size=10))
    st.plotly_chart(fig_mensal, use_container_width=True)

    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown('<div class="section-title">Hectares Mensais</div>', unsafe_allow_html=True)
        fig_ha_m = px.area(
            mensal, x='ano_mes', y='hectares',
            color_discrete_sequence=[VERDE_ESCURO],
            labels={'hectares': 'Hectares', 'ano_mes': ''},
        )
        layout_mobile(fig_ha_m, height=320, margin_b=70)
        fig_ha_m.update_xaxes(tickangle=45, tickfont=dict(size=10))
        st.plotly_chart(fig_ha_m, use_container_width=True)

    with col_r:
        st.markdown('<div class="section-title">Clientes Ativos por Mês</div>', unsafe_allow_html=True)
        fig_cli_m = px.line(
            mensal, x='ano_mes', y='clientes',
            color_discrete_sequence=[LARANJA], markers=True,
            labels={'clientes': 'Clientes Ativos', 'ano_mes': ''},
        )
        layout_mobile(fig_cli_m, height=320, margin_b=70)
        fig_cli_m.update_xaxes(tickangle=45, tickfont=dict(size=10))
        st.plotly_chart(fig_cli_m, use_container_width=True)


# ───────────────────────────────────────────────────────────────────
# ABA 6 — SAFRAS
# ───────────────────────────────────────────────────────────────────

with tab_safras:
    # Safras order
    safra_order = [
        'Safra Inverno 2023', 'Safra 2023',
        'Safra Verão 2024', 'Safrinha 2024', 'Safra Inverno 2024', 'Safra 2024',
        'Safra Verão 2025', 'Safrinha 2025', 'Safra Inverno 2025', 'Safra 2025',
        'Safra Verão 2026', 'Safrinha 2026', 'Safra Inverno 2026', 'Safra 2026',
        'Outros Serviços',
    ]

    safra_df = (
        df[df['is_silagem']].groupby('safra').agg(
            hectares=('quantidade', 'sum'),
            faturamento=('valor_bruto', 'sum'),
            clientes=('cliente', 'nunique'),
            vendas=('num_venda', 'nunique'),
        ).reset_index()
    )
    safra_df['receita_ha'] = safra_df['faturamento'] / safra_df['hectares']
    # Sort by safra_order
    safra_df['_order'] = safra_df['safra'].apply(
        lambda s: safra_order.index(s) if s in safra_order else 99
    )
    safra_df = safra_df.sort_values('_order').drop(columns='_order')

    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown('<div class="section-title">Hectares por Safra</div>', unsafe_allow_html=True)
        fig_sha = px.bar(
            safra_df, x='safra', y='hectares',
            color='safra', color_discrete_sequence=PALETTE,
            text=safra_df['hectares'].apply(lambda v: fmt_num(v, 1)),
        )
        fig_sha.update_traces(textposition='outside', textfont_size=11)
        layout_mobile(fig_sha, height=420, margin_b=110)
        fig_sha.update_layout(showlegend=False, xaxis_title="", yaxis_title="Hectares")
        fig_sha.update_xaxes(tickangle=35, tickfont=dict(size=10))
        st.plotly_chart(fig_sha, use_container_width=True)

    with col_r:
        st.markdown('<div class="section-title">Receita por Hectare por Safra</div>', unsafe_allow_html=True)
        fig_sha_r = px.bar(
            safra_df, x='safra', y='receita_ha',
            color='safra', color_discrete_sequence=PALETTE,
            text=safra_df['receita_ha'].apply(fmt_brl),
        )
        fig_sha_r.update_traces(textposition='outside', textfont_size=11)
        layout_mobile(fig_sha_r, height=420, margin_b=110)
        fig_sha_r.update_layout(showlegend=False, xaxis_title="", yaxis_title="R$/ha")
        fig_sha_r.update_xaxes(tickangle=35, tickfont=dict(size=10))
        st.plotly_chart(fig_sha_r, use_container_width=True)

    st.markdown('<div class="section-title">Resumo por Safra</div>', unsafe_allow_html=True)
    safra_show = safra_df.copy()
    safra_show['faturamento'] = safra_show['faturamento'].apply(fmt_brl)
    safra_show['hectares']    = safra_show['hectares'].apply(lambda v: fmt_num(v, 1))
    safra_show['receita_ha']  = safra_show['receita_ha'].apply(fmt_brl)
    safra_show = safra_show.rename(columns={
        'safra': 'Safra', 'hectares': 'Hectares', 'faturamento': 'Faturamento',
        'clientes': 'Clientes', 'vendas': 'Nº Vendas', 'receita_ha': 'Receita/ha',
    })
    st.dataframe(safra_show[['Safra', 'Hectares', 'Faturamento', 'Receita/ha', 'Clientes', 'Nº Vendas']],
                 use_container_width=True, hide_index=True)

    # Top clientes por safra
    st.markdown('<div class="section-title">Top Clientes por Safra (Silagem)</div>', unsafe_allow_html=True)
    safras_com_ha = safra_df[safra_df['safra'] != 'Outros Serviços']['safra'].tolist()
    safra_cli_sel = st.selectbox("Selecionar safra", safras_com_ha if safras_com_ha else ['Todos'])
    if safra_cli_sel:
        saf_cli = (
            df[(df['safra'] == safra_cli_sel) & df['is_silagem']]
            .groupby('cliente').agg(
                hectares=('quantidade', 'sum'),
                faturamento=('valor_bruto', 'sum'),
            ).sort_values('hectares', ascending=False).head(15).reset_index()
        )
        fig_saf_cli = px.bar(
            saf_cli.sort_values('hectares'),
            x='hectares', y='cliente', orientation='h',
            color='faturamento', color_continuous_scale='Greens',
            text=saf_cli.sort_values('hectares')['hectares'].apply(lambda v: fmt_num(v, 1)),
        )
        fig_saf_cli.update_traces(textposition='outside', textfont_size=11)
        layout_mobile(fig_saf_cli, height=440, margin_b=10)
        fig_saf_cli.update_layout(coloraxis_colorbar_title="Faturamento",
            xaxis_title="Hectares", yaxis_title="")
        st.plotly_chart(fig_saf_cli, use_container_width=True)


# ───────────────────────────────────────────────────────────────────
# ABA 7 — DADOS BRUTOS
# ───────────────────────────────────────────────────────────────────

with tab_dados:
    st.markdown('<div class="section-title">Dados Filtrados</div>', unsafe_allow_html=True)

    col_srch, col_exp = st.columns([3, 1])
    with col_srch:
        search = st.text_input("🔍 Buscar em qualquer campo", placeholder="Nome do cliente, cidade, produto...")
    with col_exp:
        st.markdown("<br>", unsafe_allow_html=True)
        csv_data = df.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig')
        st.download_button("⬇️ Exportar CSV", data=csv_data,
                           file_name="agrosilagem_dados.csv", mime="text/csv")

    show_df = df.copy()
    if search:
        mask = (
            show_df['cliente'].str.contains(search, case=False, na=False) |
            show_df['cidade'].str.contains(search, case=False, na=False) |
            show_df['produto'].str.contains(search, case=False, na=False) |
            show_df['safra'].str.contains(search, case=False, na=False)
        )
        show_df = show_df[mask]

    show_df_fmt = show_df[[
        'num_venda', 'data_venda', 'cliente', 'cidade', 'categoria',
        'produto', 'safra', 'quantidade', 'hectares', 'valor_bruto', 'valor_liquido'
    ]].copy()
    show_df_fmt['data_venda']   = show_df_fmt['data_venda'].dt.strftime('%d/%m/%Y')
    show_df_fmt['valor_bruto']  = show_df_fmt['valor_bruto'].apply(fmt_brl)
    show_df_fmt['valor_liquido']= show_df_fmt['valor_liquido'].apply(fmt_brl)
    show_df_fmt['quantidade']   = show_df_fmt['quantidade'].apply(lambda v: fmt_num(v, 2))
    show_df_fmt['hectares']     = show_df_fmt['hectares'].apply(lambda v: fmt_num(v, 2) if v > 0 else '-')

    show_df_fmt.columns = [
        'Nº Venda', 'Data', 'Cliente', 'Cidade', 'Categoria',
        'Produto', 'Safra', 'Qtd', 'Hectares', 'Valor Bruto', 'Valor Líquido'
    ]

    st.caption(f"Exibindo {len(show_df_fmt):,} de {len(df):,} registros filtrados")
    st.dataframe(show_df_fmt, use_container_width=True, hide_index=True, height=500)


# ───────────────────────────────────────────────────────────────────
# ABA 8 — INSIGHTS
# ───────────────────────────────────────────────────────────────────

with tab_insights:
    st.markdown('<div class="section-title">💡 Insights Automáticos</div>', unsafe_allow_html=True)

    # Top cliente
    top1 = cli_df.iloc[0] if len(cli_df) > 0 else None
    # Concentração top 10
    fat_top10 = cli_df.head(10)['faturamento'].sum()
    conc_pct  = fat_top10 / fat_total * 100 if fat_total > 0 else 0
    # Melhor mês
    melhor_mes = mensal.sort_values('faturamento', ascending=False).iloc[0] if len(mensal) > 0 else None
    # Crescimento último mês
    if len(mensal) >= 2:
        ult  = mensal.iloc[-1]['faturamento']
        pen  = mensal.iloc[-2]['faturamento']
        cresc = (ult - pen) / pen * 100 if pen > 0 else 0
    else:
        cresc = 0
    # Melhor equipamento de silagem
    sil_eq = (
        df[df['is_silagem']].groupby('produto')
        .agg(ha=('quantidade', 'sum'), fat=('valor_bruto', 'sum'))
        .reset_index()
    )
    sil_eq['rha'] = sil_eq['fat'] / sil_eq['ha']

    def insight(texto, cls=""):
        return f'<div class="insight-box {cls}">{texto}</div>'

    insights = []

    if top1 is not None:
        insights.append(insight(
            f"🏆 <b>Maior cliente:</b> <b>{top1['cliente']}</b> ({top1['cidade']}) — "
            f"{fmt_brl(top1['faturamento'])} ({top1['hectares']:.0f} ha)"
        ))

    insights.append(insight(
        f"📊 <b>Concentração:</b> Os 10 maiores clientes respondem por "
        f"<b>{conc_pct:.1f}%</b> do faturamento total ({fmt_brl(fat_top10)})",
        cls="alerta" if conc_pct > 60 else ""
    ))

    if melhor_mes is not None:
        insights.append(insight(
            f"📅 <b>Melhor mês:</b> <b>{melhor_mes['ano_mes']}</b> — "
            f"{fmt_brl(melhor_mes['faturamento'])} ({melhor_mes['vendas']:.0f} vendas)"
        ))

    if abs(cresc) > 0:
        sinal = "📈" if cresc > 0 else "📉"
        cls_c = "" if cresc > 0 else "alerta"
        insights.append(insight(
            f"{sinal} <b>Variação último mês:</b> "
            f"<b>{cresc:+.1f}%</b> vs mês anterior",
            cls=cls_c
        ))

    if len(sil_eq) > 0:
        best_eq = sil_eq.sort_values('rha', ascending=False).iloc[0]
        insights.append(insight(
            f"🚜 <b>Equipamento mais rentável:</b> <b>{best_eq['produto']}</b> — "
            f"{fmt_brl(best_eq['rha'])}/ha "
            f"({fmt_num(best_eq['ha'], 1)} ha cortados)"
        ))

    # Cidades com alto potencial
    cid_por_ha = cid_df[cid_df['hectares'] > 0].sort_values('hectares', ascending=False)
    if len(cid_por_ha) > 0:
        top_cid_ha = cid_por_ha.iloc[0]
        insights.append(insight(
            f"📍 <b>Maior volume de hectares:</b> <b>{top_cid_ha['cidade']}</b> — "
            f"{fmt_num(top_cid_ha['hectares'], 1)} ha | {fmt_brl(top_cid_ha['faturamento'])}"
        ))

    # Clientes com alto ticket
    top_ticket = cli_df[cli_df['hectares'] > 10].sort_values('ticket_medio_ha', ascending=False)
    if len(top_ticket) > 0:
        t = top_ticket.iloc[0]
        insights.append(insight(
            f"💰 <b>Maior ticket médio/ha:</b> <b>{t['cliente']}</b> — "
            f"{fmt_brl(t['ticket_medio_ha'])}/ha ({fmt_num(t['hectares'], 0)} ha)"
        ))

    # Clientes com pouco volume mas alto ticket
    oportunidades = cli_df[
        (cli_df['hectares'] > 0) &
        (cli_df['hectares'] < cli_df['hectares'].quantile(0.3)) &
        (cli_df['ticket_medio_ha'] > cli_df['ticket_medio_ha'].quantile(0.7))
    ]
    if len(oportunidades) > 0:
        insights.append(insight(
            f"🎯 <b>Oportunidade de crescimento:</b> {len(oportunidades)} clientes com "
            f"alto ticket médio mas baixo volume — potencial de expansão.",
            cls="alerta"
        ))

    # Ticket médio x safra
    if len(safra_df) > 1:
        best_safra = safra_df[safra_df['safra'] != 'Outros Serviços'].sort_values('receita_ha', ascending=False)
        if len(best_safra) > 0:
            bs = best_safra.iloc[0]
            insights.append(insight(
                f"🌱 <b>Safra mais lucrativa (R$/ha):</b> <b>{bs['safra']}</b> — "
                f"{fmt_brl(bs['receita_ha'])}/ha | {fmt_num(bs['hectares'], 1)} ha"
            ))

    for ins in insights:
        st.markdown(ins, unsafe_allow_html=True)

    # Resumo executivo
    st.markdown('<div class="section-title">📋 Resumo Executivo</div>', unsafe_allow_html=True)
    st.markdown(f"""
| Indicador | Valor |
|-----------|-------|
| **Faturamento Total Bruto** | {fmt_brl(fat_total)} |
| **Receita Líquida Total** | {fmt_brl(liq_total)} |
| **Margem Bruta** | {(liq_total/fat_total*100 if fat_total > 0 else 0):.1f}% |
| **Total de Clientes** | {total_clientes:,} |
| **Total de Vendas** | {num_vendas:,} |
| **Total de Hectares Cortados** | {fmt_num(total_ha, 1)} |
| **Receita Média por Hectare** | {fmt_brl(rec_ha)} |
| **Ticket Médio / Venda (ha)** | {fmt_brl(ticket_medio)} |
| **Período** | Ago/2023 — Mai/2026 |
""")

    # Footer
    st.markdown("---")
    st.caption(
        f"Atualizado em {datetime.now().strftime('%d/%m/%Y às %H:%M')} | "
        f"Base de dados: {len(df_raw):,} registros | Agrosilagem © 2024–2026"
    )
