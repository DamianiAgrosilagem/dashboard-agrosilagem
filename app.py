"""
Dashboard Comercial e Financeiro
AGROSILAGEM SERVICOS AGROPECUARIOS E TRANSPORTES LTDA
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pdfplumber
import re
import io
from pathlib import Path
from datetime import datetime

st.set_page_config(
    page_title="Agrosilagem — Dashboard Comercial",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Paleta ──────────────────────────────────────────────────────────────────
VERDE_ESCURO = "#1B5E20"
VERDE_CLARO  = "#4CAF50"
AMARELO      = "#F9A825"
LARANJA      = "#E65100"
AZUL         = "#0D47A1"
VERMELHO     = "#C62828"

PALETTE = [
    "#2E7D32","#1565C0","#E65100","#6A1B9A",
    "#00838F","#AD1457","#F57F17","#4E342E",
    "#37474F","#558B2F","#0277BD","#D84315",
]

# ─── Coordenadas das cidades ─────────────────────────────────────────────────
CIDADES_COORDS = {
    "Júlio De Castilhos":(-29.2247,-53.6819),"Paraí":(-28.5897,-51.7803),
    "Boa Vista Do Cadeado":(-28.6186,-53.8303),"Condor":(-28.2264,-53.4875),
    "Rio Grande":(-32.0350,-52.0986),"Salto Do Jacuí":(-28.9017,-53.2133),
    "Guabiju":(-28.5428,-51.7442),"Ibiraiaras":(-28.3747,-51.6467),
    "São Jorge":(-28.4944,-51.2481),"Hulha Negra":(-31.4003,-53.8736),
    "Candiota":(-31.5578,-53.6758),"Cruz Alta":(-28.6389,-53.6064),
    "Santa Maria":(-29.6869,-53.8019),"Porto Alegre":(-30.0346,-51.2177),
    "Passo Fundo":(-28.2622,-52.4064),"Santiago":(-29.1897,-54.8658),
    "Ijuí":(-28.3878,-53.9147),"Santo Ângelo":(-28.2997,-54.2631),
    "Cachoeira Do Sul":(-30.0353,-52.8931),"Pelotas":(-31.7654,-52.3376),
    "Bagé":(-31.3289,-54.1056),"Uruguaiana":(-29.7542,-57.0883),
    "Alegrete":(-29.7833,-55.7919),"Santa Rosa":(-27.8711,-54.4814),
    "Erechim":(-27.6347,-52.2742),"Caxias Do Sul":(-29.1681,-51.1794),
    "Setubinha-Mg":(-17.9397,-42.2022),"Malacacheta-Mg":(-17.8392,-42.0792),
    "Não-Me-Toque":(-28.4569,-52.8194),"Tapera":(-28.6261,-52.8697),
    "Selbach":(-28.6422,-52.9536),"Colorado":(-28.5494,-52.7025),
    "Victor Graeff":(-28.5072,-52.7736),"Quinze De Novembro":(-28.7347,-53.0972),
    "Ibirubá":(-28.6289,-53.0872),"Carazinho":(-28.2839,-52.7881),
    "Tupanciretã":(-29.0842,-53.8414),"Jóia":(-28.6539,-54.1158),
    "Palmeira Das Missões":(-27.8989,-53.3131),"Sarandi":(-27.9428,-52.9247),
    "Espumoso":(-28.7272,-52.8514),"Lagoa Dos Três Cantos":(-28.5789,-52.7953),
    "Soledade":(-28.8272,-52.5114),"Fontoura Xavier":(-28.9786,-52.3431),
    "Campos Borges":(-28.8669,-53.0089),"Fortaleza Dos Valos":(-28.7994,-53.3008),
    "Boa Vista Do Incra":(-28.6253,-53.1047),"Saldanha Marinho":(-28.4364,-53.0325),
    "Lagoa Dos Três Cantos":(-28.5789,-52.7953),"Panambi":(-28.3017,-53.5011),
    "Augusto Pestana":(-28.4397,-54.0036),"Chiapetta":(-27.9756,-53.9494),
    "Tenente Portela":(-27.3711,-53.7583),"Três Passos":(-27.4553,-53.9253),
    "Horizontina":(-27.6233,-54.3078),"Cândido Godói":(-27.9467,-54.2897),
    "Giruá":(-28.0314,-54.3536),"Coronel Bicaco":(-27.7208,-53.7106),
}

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #1B5E20; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }

    /* Campos de input na sidebar — fundo claro para legibilidade */
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] .stDateInput input,
    [data-testid="stSidebar"] [data-baseweb="input"] input,
    [data-testid="stSidebar"] [data-baseweb="select"] div,
    [data-testid="stSidebar"] [data-baseweb="tag"],
    [data-testid="stSidebar"] [data-baseweb="popover"] {
        background-color: rgba(255,255,255,0.15) !important;
        color: #FFFFFF !important;
        border-color: rgba(255,255,255,0.4) !important;
    }
    [data-testid="stSidebar"] [data-baseweb="select"] [data-baseweb="tag"] {
        background-color: rgba(255,255,255,0.25) !important;
        color: #FFFFFF !important;
    }
    /* Placeholder dos multiselects */
    [data-testid="stSidebar"] [data-baseweb="select"] span {
        color: rgba(255,255,255,0.7) !important;
    }
    /* Datas */
    [data-testid="stSidebar"] .stDateInput > div > div {
        background-color: rgba(255,255,255,0.15) !important;
        border-color: rgba(255,255,255,0.4) !important;
    }
    [data-testid="stSidebar"] .stDateInput input {
        color: #FFFFFF !important;
        background-color: transparent !important;
    }
    /* Slider */
    [data-testid="stSidebar"] .stSlider [data-testid="stTickBarMin"],
    [data-testid="stSidebar"] .stSlider [data-testid="stTickBarMax"] {
        color: rgba(255,255,255,0.8) !important;
    }

    .kpi-card {
        background: linear-gradient(135deg, #2E7D32, #1B5E20);
        border-radius: 12px; padding: 18px 20px; color: white;
        text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.2); margin-bottom: 8px;
    }
    .kpi-card.azul    { background: linear-gradient(135deg,#1565C0,#0D47A1); }
    .kpi-card.laranja { background: linear-gradient(135deg,#E65100,#BF360C); }
    .kpi-card.roxo    { background: linear-gradient(135deg,#6A1B9A,#4A148C); }
    .kpi-card.teal    { background: linear-gradient(135deg,#00838F,#006064); }
    .kpi-card.vermelho{ background: linear-gradient(135deg,#C62828,#B71C1C); }
    .kpi-card .kpi-value { font-size: 1.7rem; font-weight: 700; margin: 6px 0; }
    .kpi-card .kpi-label { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; opacity: 0.85; }
    .kpi-card .kpi-delta { font-size: 0.8rem; margin-top: 4px; opacity: 0.9; }

    .alerta-concentracao {
        background: #FFF3E0; border-left: 5px solid #E65100;
        border-radius: 8px; padding: 12px 16px; margin: 8px 0; color: #BF360C;
    }
    .alerta-ok {
        background: #E8F5E9; border-left: 5px solid #4CAF50;
        border-radius: 8px; padding: 12px 16px; margin: 8px 0; color: #1B5E20;
    }
    .section-title {
        font-size: 1.05rem; font-weight: 600; color: #1B5E20;
        border-left: 4px solid #4CAF50; padding-left: 10px; margin: 18px 0 12px 0;
    }
    .insight-box {
        background: #E8F5E9; border-left: 4px solid #4CAF50;
        border-radius: 6px; padding: 12px 16px; margin: 6px 0;
        font-size: 0.88rem; color: #1B5E20;
    }
    .insight-box.alerta { background:#FFF3E0; border-left-color:#E65100; color:#BF360C; }
    .main-header {
        background: linear-gradient(90deg,#1B5E20,#2E7D32);
        padding: 16px 24px; border-radius: 10px; color: white; margin-bottom: 20px;
    }
    .main-header h1 { margin: 0; font-size: 1.4rem; }
    .main-header p  { margin: 2px 0; font-size: 0.82rem; opacity: 0.85; }
    .block-container { padding-top: 1rem; }
    .fidelidade-badge {
        display: inline-block; padding: 3px 10px; border-radius: 12px;
        font-size: 0.8rem; font-weight: 600; margin: 2px;
    }
    @media (max-width: 768px) {
        [data-testid="column"] { width:100%!important; flex:1 1 100%!important; min-width:100%!important; }
        .kpi-card .kpi-value { font-size: 1.3rem; }
        .block-container { padding: 0.5rem 0.5rem 2rem !important; }
    }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# PATHS E EXTRAÇÃO
# ═══════════════════════════════════════════════════════════════════
BASE_DIR    = Path(__file__).parent
DATA_DIR    = BASE_DIR / "data"
PDF_DIR     = BASE_DIR.parent
VENDAS_FILE = DATA_DIR / "vendas.csv.gz"


def parse_br_number(s):
    if not s:
        return 0.0
    s = str(s).strip().replace('\n','').replace(' ','').replace('.','').replace(',','.')
    try: return float(s)
    except: return 0.0


def categorize_produto(produto):
    p = str(produto).upper()
    if any(k in p for k in ['CORTE DE SILAGEM','CLAAS','FR 500','FR BIG','KRONE']):
        return 'Corte de Silagem'
    if 'FRETE TERCEIROS' in p: return 'Frete Terceiros'
    if any(k in p for k in ['M.BENZ','FORD CARGO','VOLVO','SCANIA']): return 'Caminhões'
    if 'TRATOR' in p: return 'Tratores'
    if 'DIESEL' in p: return 'Ajuste de Diesel'
    if 'KM' in p: return 'KM Excedente'
    return 'Outros'


def extract_safra(d):
    if not d: return 'Outros Serviços'
    d = str(d).upper()
    mapping = [
        (['INVERNO','2023'],'Safra Inverno 2023'),(['INVERNO','2024'],'Safra Inverno 2024'),
        (['INVERNO','2025'],'Safra Inverno 2025'),(['INVERNO','2026'],'Safra Inverno 2026'),
        (['VER','2025'],'Safra Verão 2025'),(['VER','2026'],'Safra Verão 2026'),
        (['SAFRINHA','2024'],'Safrinha 2024'),(['SAFRINHA','2025'],'Safrinha 2025'),
        (['SAFRINHA','2026'],'Safrinha 2026'),
    ]
    for keys, label in mapping:
        if all(k in d for k in keys): return label
    for yr in ['2023','2024','2025','2026']:
        if yr in d: return f'Safra {yr}'
    return 'Outros Serviços'


@st.cache_data(show_spinner=False)
def extract_pdf1(path):
    rows = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                for row in table:
                    if not row or len(row) < 8: continue
                    r0 = str(row[0]).strip().replace('\n','') if row[0] else ''
                    if not r0 or not re.match(r'^\d+$', r0) or len(r0) > 5: continue
                    rows.append(row[:8])
    return rows


@st.cache_data(show_spinner=False)
def extract_pdf2(path):
    rows, cur_v, cur_c = [], None, None
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                for row in table:
                    if not row or len(row) < 8: continue
                    r0=str(row[0]).replace('\n',' ').strip() if row[0] else ''
                    r1=str(row[1]).replace('\n',' ').strip() if row[1] else ''
                    r2=str(row[2]).replace('\n',' ').strip() if row[2] else ''
                    r3=str(row[3]).replace('\n',' ').strip() if row[3] else ''
                    if 'Número' in r0 or 'Total geral' in r0: continue
                    if 'Total' in r0 or 'Total' in r1: continue
                    if re.match(r'^\d+$', r0):
                        cur_v, cur_c = int(r0), r1
                        data = r2 if re.match(r'\d{2}/\d{2}/\d{4}',r2) else ''
                        detalhes = r3
                    elif cur_v:
                        data = r2 if re.match(r'\d{2}/\d{2}/\d{4}',r2) else ''
                        detalhes = r3 if r3 else (r0 if r0 else r1)
                    else: continue
                    vb = parse_br_number(row[5]); vl = parse_br_number(row[7])
                    if vb > 0 and detalhes:
                        rows.append({'num_venda':cur_v,'cliente':cur_c,'data_venda':data,
                                     'detalhes':detalhes,'quantidade':parse_br_number(row[4]),
                                     'valor_bruto':vb,'valor_unitario':parse_br_number(row[6]),'valor_liquido':vl})
    return rows


@st.cache_data(show_spinner=False)
def build_dataset():
    if VENDAS_FILE.exists():
        df = pd.read_csv(VENDAS_FILE, compression='gzip', parse_dates=['data_venda'])
        df['is_silagem'] = df['is_silagem'].astype(bool)
        df['hectares']   = df['hectares'].fillna(0)
        return df
    pdf1 = PDF_DIR / "Relatório de Vendas por Safra.pdf"
    pdf2 = PDF_DIR / "RESUMO DE VENDAS.pdf"
    if not pdf1.exists() or not pdf2.exists():
        st.error("PDFs não encontrados. Coloque-os em: " + str(PDF_DIR))
        st.stop()
    with st.spinner("Extraindo dados dos PDFs..."):
        rows1 = extract_pdf1(str(pdf1))
        rows2 = extract_pdf2(str(pdf2))
    df1 = []
    for row in rows1:
        num = str(row[0]).strip()
        if not re.match(r'^\d+$', num): continue
        produto = str(row[4]).replace('\n',' ').strip()
        safra   = str(row[5]).replace('\n',' ').strip()
        df1.append({
            'num_venda':int(num),'data_venda':str(row[1]).replace('\n',' ').strip(),
            'cliente':str(row[2]).replace('\n',' ').strip(),'cidade':str(row[3]).replace('\n',' ').strip(),
            'produto':produto,'safra_raw':safra,'quantidade':parse_br_number(row[6]),
            'valor_bruto':parse_br_number(row[7]),'categoria':categorize_produto(produto),
            'safra':extract_safra(safra),
            'is_silagem':any(k in produto.upper() for k in ['CORTE DE SILAGEM','CLAAS','FR 500','FR BIG','KRONE']),
        })
    df = pd.DataFrame(df1)
    df['data_venda'] = pd.to_datetime(df['data_venda'], format='%d/%m/%Y', errors='coerce')
    df['cidade'] = df['cidade'].str.title().str.strip()
    df2 = pd.DataFrame(rows2)
    vl = df2.groupby('num_venda')['valor_liquido'].sum().reset_index()
    vl.columns = ['num_venda','valor_liquido_total_venda']
    df = df.merge(vl, on='num_venda', how='left')
    vb = df.groupby('num_venda')['valor_bruto'].transform('sum')
    df['valor_liquido'] = df['valor_bruto'] / vb.replace(0,1) * df['valor_liquido_total_venda'].fillna(df['valor_bruto'])
    df['hectares'] = df.apply(lambda r: r['quantidade'] if r['is_silagem'] else 0.0, axis=1)
    DATA_DIR.mkdir(exist_ok=True)
    df.to_csv(VENDAS_FILE, index=False, compression='gzip')
    return df


# ═══════════════════════════════════════════════════════════════════
# IMPORTAÇÃO DE ARQUIVO (Excel / CSV do Conta Azul)
# ═══════════════════════════════════════════════════════════════════
def import_conta_azul(uploaded_file, merge=True):
    """Processa arquivo Excel/CSV exportado do Conta Azul. Retorna (df_final, erro)."""
    try:
        name = uploaded_file.name.lower()
        if name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(uploaded_file, dtype=str)
        else:
            try:
                df = pd.read_csv(uploaded_file, encoding='utf-8-sig', sep=None, engine='python', dtype=str)
            except Exception:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, encoding='latin-1', sep=None, engine='python', dtype=str)
    except Exception as e:
        return None, f"Erro ao ler arquivo: {e}"

    if df.empty:
        return None, "Arquivo vazio."

    df.columns = [str(c).strip().lower() for c in df.columns]

    MAPS = {
        'num_venda':    ['número da venda','número','numero','num','nf','nota fiscal',
                         'pedido','venda','num. venda','cod. venda','código','codigo'],
        'data_venda':   ['data da venda','data','emissão','emissao','data de emissão',
                         'data emissão','data emissao','data venda'],
        'cliente':      ['cliente','nome','razão social','razao social','nome do cliente',
                         'comprador','destinatário','destinatario'],
        'cidade':       ['cidade do cliente','cidade','município','municipio','local','localidade'],
        'produto':      ['nome do produto/serviço','produto/serviço','produto','serviço',
                         'servico','descrição','descricao','item','discriminação','discriminacao'],
        'safra_raw':    ['detalhes do item','safra','observação','observacao','obs',
                         'referência','referencia','complemento','informação adicional'],
        'quantidade':   ['quantidade de itens','quantidade','qtd','qtd.','qtde','qtde.'],
        'valor_bruto':  ['valor bruto','v. bruto','total','valor total','valor',
                         'preço total','preco total','total bruto'],
        'valor_liquido':['valor líquido','valor liquido','v. líquido','v. liquido',
                         'líquido','liquido','valor liq','total líquido'],
    }

    col_map = {}
    for target, candidates in MAPS.items():
        for cand in candidates:
            if cand in df.columns:
                col_map[target] = cand
                break

    # valor_bruto é opcional — usa valor_liquido como fallback
    required = ['num_venda', 'data_venda', 'cliente', 'produto']
    if 'valor_bruto' not in col_map and 'valor_liquido' not in col_map:
        required.append('valor_bruto')  # força erro descritivo

    missing = [r for r in required if r not in col_map]
    if missing:
        avail = ', '.join(df.columns.tolist())
        return None, (f"Colunas obrigatórias não encontradas: {missing}.\n"
                      f"Colunas no arquivo: {avail}")

    out = pd.DataFrame()
    for target, src in col_map.items():
        out[target] = df[src]

    if 'safra_raw'     not in out.columns: out['safra_raw']     = out['produto']
    if 'cidade'        not in out.columns: out['cidade']        = ''
    if 'quantidade'    not in out.columns: out['quantidade']    = '1'
    # Se não há valor_bruto, usa valor_liquido no lugar
    if 'valor_bruto'   not in out.columns: out['valor_bruto']   = out['valor_liquido']
    if 'valor_liquido' not in out.columns: out['valor_liquido'] = out['valor_bruto']

    out['num_venda']    = pd.to_numeric(out['num_venda'].astype(str).str.replace(r'\D','',regex=True), errors='coerce').fillna(0).astype(int)
    out['data_venda']   = pd.to_datetime(out['data_venda'], dayfirst=True, errors='coerce')
    out['quantidade']   = out['quantidade'].apply(parse_br_number)
    out['valor_bruto']  = out['valor_bruto'].apply(parse_br_number)
    out['valor_liquido']= out['valor_liquido'].apply(parse_br_number)

    out = out[out['data_venda'].notna() & (out['valor_bruto'] > 0)].copy()
    if out.empty:
        return None, "Nenhum registro válido encontrado após processamento."

    out['cidade']    = out['cidade'].fillna('').str.title().str.strip()
    out['cliente']   = out['cliente'].fillna('').str.strip()
    out['produto']   = out['produto'].fillna('').str.strip()
    out['safra_raw'] = out['safra_raw'].fillna('').str.strip()
    out['categoria'] = out['produto'].apply(categorize_produto)
    out['safra']     = out['safra_raw'].apply(extract_safra)
    out['is_silagem']= out['produto'].str.upper().str.contains(
                           'CORTE DE SILAGEM|CLAAS|FR 500|FR BIG|KRONE', na=False)
    out['hectares']  = out.apply(lambda r: r['quantidade'] if r['is_silagem'] else 0.0, axis=1)
    out['ano_mes']   = out['data_venda'].dt.to_period('M').astype(str)
    out['ano']       = out['data_venda'].dt.year
    out['mes']       = out['data_venda'].dt.month

    vl = out.groupby('num_venda')['valor_liquido'].sum().reset_index()
    vl.columns = ['num_venda','valor_liquido_total_venda']
    out = out.merge(vl, on='num_venda', how='left')

    if merge and VENDAS_FILE.exists():
        existing = pd.read_csv(VENDAS_FILE, compression='gzip', parse_dates=['data_venda'])
        existing['is_silagem'] = existing['is_silagem'].astype(bool)
        existing = existing[~existing['num_venda'].isin(out['num_venda'].unique())]
        out = pd.concat([existing, out], ignore_index=True)
        out = out.sort_values('data_venda').reset_index(drop=True)

    DATA_DIR.mkdir(exist_ok=True)
    out.to_csv(VENDAS_FILE, index=False, compression='gzip')
    return out, None


# ═══════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════
def fmt_brl(v):
    return f"R$ {v:,.2f}".replace(",","X").replace(".",",").replace("X",".")

def fmt_num(v, d=0):
    return f"{v:,.{d}f}".replace(",","X").replace(".",",").replace("X",".")

def kpi(label, value, cls="", delta=""):
    dh = f'<div class="kpi-delta">{delta}</div>' if delta else ""
    return f'<div class="kpi-card {cls}"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div>{dh}</div>'

def section(title):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)

def layout_mobile(fig, height=380, margin_b=60, font_size=13):
    fig.update_layout(height=height, margin=dict(l=8,r=8,t=36,b=margin_b),
        font=dict(size=font_size,family="Arial, sans-serif"),
        plot_bgcolor="white", paper_bgcolor="white",
        legend=dict(orientation="h",y=-0.22,x=0,font=dict(size=11)))
    fig.update_xaxes(tickfont=dict(size=11),title_font=dict(size=12))
    fig.update_yaxes(tickfont=dict(size=11),title_font=dict(size=12))
    return fig

SAFRA_ORDER = [
    'Safra Inverno 2023','Safra 2023',
    'Safra Verão 2024','Safrinha 2024','Safra Inverno 2024','Safra 2024',
    'Safra Verão 2025','Safrinha 2025','Safra Inverno 2025','Safra 2025',
    'Safra Verão 2026','Safrinha 2026','Safra Inverno 2026','Safra 2026',
    'Outros Serviços',
]

# ═══════════════════════════════════════════════════════════════════
# CARGA DE DADOS
# ═══════════════════════════════════════════════════════════════════
df_raw = build_dataset()
df_raw['ano_mes'] = df_raw['data_venda'].dt.to_period('M').astype(str)
df_raw['ano'] = df_raw['data_venda'].dt.year
df_raw['mes'] = df_raw['data_venda'].dt.month

# ═══════════════════════════════════════════════════════════════════
# SIDEBAR — FILTROS
# ═══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🌾 Agrosilagem")
    st.markdown("### Filtros")

    min_date = df_raw['data_venda'].min().date()
    max_date = df_raw['data_venda'].max().date()
    c1, c2 = st.columns(2)
    with c1: dt_inicio = st.date_input("De",  value=min_date, min_value=min_date, max_value=max_date, format="DD/MM/YYYY")
    with c2: dt_fim    = st.date_input("Até", value=max_date, min_value=min_date, max_value=max_date, format="DD/MM/YYYY")

    safra_sel   = st.multiselect("Safra",     sorted(df_raw['safra'].dropna().unique()),     default=[], placeholder="Todas as safras")
    cat_sel     = st.multiselect("Categoria", sorted(df_raw['categoria'].dropna().unique()), default=[], placeholder="Todas as categorias")
    cidade_sel  = st.multiselect("Cidade",    sorted(df_raw['cidade'].dropna().unique()),    default=[], placeholder="Todas as cidades")
    cliente_sel = st.multiselect("Cliente",   sorted(df_raw['cliente'].dropna().unique()),   default=[], placeholder="Todos os clientes")

    max_ha  = int(df_raw[df_raw['is_silagem']]['quantidade'].max())
    ha_range = st.slider("Faixa de Hectares", 0, max_ha, (0, max_ha))

    st.markdown("---")
    modo_escuro = st.toggle("🌙 Modo Escuro", value=False)
    st.markdown("---")
    if st.button("🔄 Atualizar Dados"):
        if VENDAS_FILE.exists(): VENDAS_FILE.unlink()
        st.cache_data.clear(); st.rerun()

    st.markdown("---")
    with st.expander("📤 Importar do Conta Azul"):
        st.markdown("""
**Como exportar do Conta Azul:**
1. Acesse **Vendas → Relatórios**
2. Escolha o período desejado
3. Clique em **Exportar → Excel**
4. Faça o upload abaixo
""")
        st.caption("Aceita .xlsx, .xls ou .csv")
        arq = st.file_uploader(
            "Selecionar arquivo", type=['xlsx','xls','csv'],
            label_visibility='collapsed', key='uploader_ca'
        )
        merge_opt = st.checkbox(
            "Mesclar com histórico existente", value=True,
            help="Marcado: adiciona os novos registros sem apagar os anteriores.\n"
                 "Desmarcado: substitui todos os dados."
        )
        if arq:
            with st.spinner("Processando..."):
                df_imp, erro = import_conta_azul(arq, merge=merge_opt)
            if erro:
                st.error(f"❌ {erro}")
            else:
                min_d = df_imp['data_venda'].min().strftime('%d/%m/%Y')
                max_d = df_imp['data_venda'].max().strftime('%d/%m/%Y')
                st.success(f"✅ {len(df_imp):,} registros no total")
                st.caption(f"Período: {min_d} → {max_d}")
                if st.button("🔄 Recarregar Dashboard", key="btn_reload_imp"):
                    st.cache_data.clear(); st.rerun()

# ─── Modo Escuro ─────────────────────────────────────────────────
if modo_escuro:
    st.markdown("""
    <style>
        .stApp { background-color: #121212 !important; color: #E0E0E0 !important; }
        .block-container { background-color: #121212 !important; }
        .section-title { color: #81C784 !important; border-left-color: #81C784 !important; }
        .stTabs [data-baseweb="tab"] { color: #81C784 !important; }
        [data-testid="stMetric"] { color: #E0E0E0 !important; }
        div[data-testid="stDataFrame"] { background: #1E1E1E !important; }
    </style>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# FILTROS APLICADOS
# ═══════════════════════════════════════════════════════════════════
df = df_raw.copy()
df = df[df['data_venda'].dt.date.between(dt_inicio, dt_fim)]
if safra_sel:   df = df[df['safra'].isin(safra_sel)]
if cat_sel:     df = df[df['categoria'].isin(cat_sel)]
if cidade_sel:  df = df[df['cidade'].isin(cidade_sel)]
if cliente_sel: df = df[df['cliente'].isin(cliente_sel)]
mask_ha = (~df['is_silagem']) | (df['quantidade'].between(ha_range[0], ha_range[1]))
df = df[mask_ha]

# ═══════════════════════════════════════════════════════════════════
# KPIs
# ═══════════════════════════════════════════════════════════════════
fat_total = df['valor_bruto'].sum()
liq_total = df['valor_liquido'].sum()
total_cli = df['cliente'].nunique()
total_ha  = df['hectares'].sum()
rec_ha    = fat_total / total_ha if total_ha > 0 else 0
num_vendas = df['num_venda'].nunique()

vendas_agg = df.groupby('num_venda').agg(fat=('valor_bruto','sum'), ha=('hectares','sum')).reset_index()
vendas_ha  = vendas_agg[vendas_agg['ha'] > 0]
ticket_medio = (vendas_ha['fat'] / vendas_ha['ha']).mean() if len(vendas_ha) > 0 else 0

cli_df = (
    df.groupby('cliente').agg(
        faturamento=('valor_bruto','sum'), liquido=('valor_liquido','sum'),
        hectares=('hectares','sum'), num_vendas=('num_venda','nunique'),
        cidade=('cidade', lambda x: x.mode()[0] if len(x)>0 else ''),
    ).sort_values('faturamento', ascending=False).reset_index()
)
cli_df['ticket_medio_ha'] = cli_df.apply(
    lambda r: r['faturamento']/r['hectares'] if r['hectares']>0 else 0, axis=1)
cli_df['rank'] = range(1, len(cli_df)+1)

fat_top5  = cli_df.head(5)['faturamento'].sum()
fat_top10 = cli_df.head(10)['faturamento'].sum()
conc5_pct = fat_top5 / fat_total * 100 if fat_total > 0 else 0

# ═══════════════════════════════════════════════════════════════════
# CABEÇALHO
# ═══════════════════════════════════════════════════════════════════
st.markdown("""
<div class="main-header">
    <div style="font-size:2.2rem">🌾</div>
    <div>
        <h1>Dashboard Comercial & Financeiro</h1>
        <p>AGROSILAGEM SERVICOS AGROPECUARIOS E TRANSPORTES LTDA &nbsp;|&nbsp; Análise de vendas e safras</p>
    </div>
</div>""", unsafe_allow_html=True)

periodo_str = f"{dt_inicio.strftime('%d/%m/%Y')} — {dt_fim.strftime('%d/%m/%Y')}"
st.caption(f"📅 Período: **{periodo_str}** &nbsp;|&nbsp; {len(df):,} registros | {num_vendas:,} vendas realizadas")

# ─── KPI Cards ───────────────────────────────────────────────────
c1,c2,c3,c4,c5,c6 = st.columns(6)
with c1: st.markdown(kpi("Faturamento Bruto", fmt_brl(fat_total)), unsafe_allow_html=True)
with c2: st.markdown(kpi("Receita Líquida", fmt_brl(liq_total), cls="azul"), unsafe_allow_html=True)
with c3: st.markdown(kpi("Ticket Médio/ha", fmt_brl(ticket_medio), cls="laranja",
                         delta=f"{len(vendas_ha)} vendas c/ ha"), unsafe_allow_html=True)
with c4: st.markdown(kpi("Total Hectares", fmt_num(total_ha,1), cls="roxo",
                         delta=fmt_brl(rec_ha)+"/ha"), unsafe_allow_html=True)
with c5: st.markdown(kpi("Clientes Ativos", fmt_num(total_cli), cls="teal",
                         delta=f"{num_vendas} vendas"), unsafe_allow_html=True)
with c6:
    cls_conc = "vermelho" if conc5_pct > 60 else "laranja" if conc5_pct > 40 else ""
    st.markdown(kpi("Concentração Top 5", f"{conc5_pct:.1f}%", cls=cls_conc,
                    delta="⚠️ Risco alto" if conc5_pct > 60 else "✅ Saudável"), unsafe_allow_html=True)

# ─── Alerta de concentração ──────────────────────────────────────
if conc5_pct > 60:
    st.markdown(f'<div class="alerta-concentracao">⚠️ <b>Atenção:</b> Os 5 maiores clientes representam <b>{conc5_pct:.1f}%</b> do faturamento ({fmt_brl(fat_top5)}). Risco de concentração elevado — considere diversificar a carteira.</div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="alerta-ok">✅ <b>Concentração saudável:</b> Top 5 clientes = {conc5_pct:.1f}% do faturamento ({fmt_brl(fat_top5)})</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# ABAS
# ═══════════════════════════════════════════════════════════════════
(tab_visao, tab_clientes, tab_produtos, tab_geo, tab_mapa,
 tab_temporal, tab_safras, tab_sazonalidade, tab_fidelidade,
 tab_projecao, tab_dados, tab_insights, tab_resumo) = st.tabs([
    "📊 Visão Geral","👥 Clientes","🚜 Produtos","📍 Cidades","🗺️ Mapa",
    "📈 Evolução Mensal","🌱 Safras","📅 Sazonalidade","🔄 Fidelidade",
    "🎯 Projeção","📋 Dados","💡 Insights","📄 Resumo Executivo",
])

# ───────────────────────────────────────────────────────────────────
# ABA 1 — VISÃO GERAL
# ───────────────────────────────────────────────────────────────────
with tab_visao:
    cat_df = df.groupby('categoria')['valor_bruto'].sum().sort_values(ascending=True).reset_index()
    col_l, col_r = st.columns(2)
    with col_l:
        section("Faturamento por Categoria")
        fig = px.bar(cat_df, x='valor_bruto', y='categoria', orientation='h',
                     color='categoria', color_discrete_sequence=PALETTE,
                     text=cat_df['valor_bruto'].apply(fmt_brl))
        fig.update_traces(textposition='outside', textfont_size=11)
        layout_mobile(fig, 340, 10)
        fig.update_layout(showlegend=False, xaxis=dict(showticklabels=False, showgrid=False),
                          xaxis_title="", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)
    with col_r:
        section("Distribuição por Categoria")
        fig2 = px.pie(cat_df, values='valor_bruto', names='categoria',
                      color_discrete_sequence=PALETTE, hole=0.45)
        fig2.update_traces(textposition='inside', textinfo='label+percent',
                           textfont_size=12, insidetextorientation='radial')
        layout_mobile(fig2, 340, 10)
        fig2.update_layout(showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    section("Faturamento Bruto vs Líquido por Categoria")
    bvsl = df.groupby('categoria').agg(bruto=('valor_bruto','sum'), liquido=('valor_liquido','sum')).sort_values('bruto',ascending=False).reset_index()
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(x=bvsl['categoria'], y=bvsl['bruto'], name='Bruto',
                          marker_color=VERDE_CLARO, text=bvsl['bruto'].apply(fmt_brl),
                          textposition='outside', textfont_size=10))
    fig3.add_trace(go.Bar(x=bvsl['categoria'], y=bvsl['liquido'], name='Líquido',
                          marker_color=AZUL, text=bvsl['liquido'].apply(fmt_brl),
                          textposition='outside', textfont_size=10))
    layout_mobile(fig3, 360, 60)
    fig3.update_layout(barmode='group', xaxis_title="", yaxis_title="R$")
    st.plotly_chart(fig3, use_container_width=True)

# ───────────────────────────────────────────────────────────────────
# ABA 2 — CLIENTES
# ───────────────────────────────────────────────────────────────────
with tab_clientes:
    n_top = st.slider("Top N clientes", 5, 50, 20, key="top_cli")
    col_l, col_r = st.columns(2)
    top_cli = cli_df.head(n_top)
    with col_l:
        section("Ranking de Faturamento")
        fig = px.bar(top_cli.sort_values('faturamento'), x='faturamento', y='cliente',
                     orientation='h', color='faturamento',
                     color_continuous_scale=['#A5D6A7','#1B5E20'],
                     text=top_cli.sort_values('faturamento')['faturamento'].apply(fmt_brl))
        fig.update_traces(textposition='outside', textfont_size=11)
        layout_mobile(fig, max(380, n_top*24), 10)
        fig.update_layout(showlegend=False, coloraxis_showscale=False,
                          xaxis=dict(showticklabels=False, showgrid=False), yaxis_title="", xaxis_title="")
        st.plotly_chart(fig, use_container_width=True)
    with col_r:
        section("Ticket Médio/ha (Top 15)")
        tm = cli_df[cli_df['hectares']>0].head(15).sort_values('ticket_medio_ha')
        fig2 = px.bar(tm, x='ticket_medio_ha', y='cliente', orientation='h',
                      color='ticket_medio_ha', color_continuous_scale=['#B3E5FC','#01579B'],
                      text=tm['ticket_medio_ha'].apply(fmt_brl))
        fig2.update_traces(textposition='outside', textfont_size=11)
        layout_mobile(fig2, 400, 10)
        fig2.update_layout(showlegend=False, coloraxis_showscale=False,
                           xaxis=dict(showticklabels=False, showgrid=False), yaxis_title="", xaxis_title="")
        st.plotly_chart(fig2, use_container_width=True)

    # ── DRILL-DOWN de cliente ──
    section("🔍 Detalhamento por Cliente")
    cli_sel = st.selectbox("Selecione um cliente para ver o histórico completo",
                           ["— Selecione —"] + cli_df['cliente'].tolist())
    if cli_sel != "— Selecione —":
        dc = df[df['cliente'] == cli_sel]
        r  = cli_df[cli_df['cliente'] == cli_sel].iloc[0]
        cc1,cc2,cc3,cc4 = st.columns(4)
        with cc1: st.metric("Faturamento Total", fmt_brl(r['faturamento']))
        with cc2: st.metric("Hectares Totais",   fmt_num(r['hectares'],1) + " ha")
        with cc3: st.metric("Ticket Médio/ha",   fmt_brl(r['ticket_medio_ha']))
        with cc4: st.metric("Nº de Vendas",      str(int(r['num_vendas'])))

        col_a, col_b = st.columns(2)
        with col_a:
            section("Faturamento por Safra")
            dc_safra = dc[dc['is_silagem']].groupby('safra').agg(
                fat=('valor_bruto','sum'), ha=('hectares','sum')).reset_index()
            dc_safra['_o'] = dc_safra['safra'].apply(lambda s: SAFRA_ORDER.index(s) if s in SAFRA_ORDER else 99)
            dc_safra = dc_safra.sort_values('_o')
            fig_dc = px.bar(dc_safra, x='safra', y='fat', color='safra',
                            color_discrete_sequence=PALETTE,
                            text=dc_safra['fat'].apply(fmt_brl))
            fig_dc.update_traces(textposition='outside', textfont_size=10)
            layout_mobile(fig_dc, 320, 80)
            fig_dc.update_layout(showlegend=False, xaxis_title="", yaxis_title="R$")
            fig_dc.update_xaxes(tickangle=35)
            st.plotly_chart(fig_dc, use_container_width=True)
        with col_b:
            section("Hectares por Safra")
            fig_dc2 = px.bar(dc_safra, x='safra', y='ha', color='safra',
                             color_discrete_sequence=PALETTE,
                             text=dc_safra['ha'].apply(lambda v: fmt_num(v,1)))
            fig_dc2.update_traces(textposition='outside', textfont_size=10)
            layout_mobile(fig_dc2, 320, 80)
            fig_dc2.update_layout(showlegend=False, xaxis_title="", yaxis_title="Hectares")
            fig_dc2.update_xaxes(tickangle=35)
            st.plotly_chart(fig_dc2, use_container_width=True)

        section("Produtos utilizados")
        dc_prod = dc.groupby('categoria')['valor_bruto'].sum().sort_values(ascending=False).reset_index()
        dc_prod['pct'] = dc_prod['valor_bruto'] / dc_prod['valor_bruto'].sum() * 100
        dc_prod['Faturamento'] = dc_prod['valor_bruto'].apply(fmt_brl)
        dc_prod['%'] = dc_prod['pct'].apply(lambda v: f"{v:.1f}%")
        st.dataframe(dc_prod[['categoria','Faturamento','%']].rename(columns={'categoria':'Categoria'}),
                     use_container_width=True, hide_index=True)

    # Bubble chart
    section("Comparativo Hectares × Faturamento")
    bubble = cli_df[cli_df['hectares']>0].head(40)
    fig_b = px.scatter(bubble, x='hectares', y='faturamento', size='faturamento',
                       color='ticket_medio_ha', hover_name='cliente',
                       color_continuous_scale='Greens', size_max=60,
                       labels={'hectares':'Hectares','faturamento':'Faturamento (R$)'},
                       text='cliente')
    fig_b.update_traces(textposition='top center', textfont_size=9)
    layout_mobile(fig_b, 460, 60)
    fig_b.update_layout(coloraxis_colorbar_title="Ticket/ha")
    st.plotly_chart(fig_b, use_container_width=True)

    section("Tabela de Clientes")
    cs = top_cli.copy()
    cs['faturamento']     = cs['faturamento'].apply(fmt_brl)
    cs['liquido']         = cs['liquido'].apply(fmt_brl)
    cs['hectares']        = cs['hectares'].apply(lambda v: fmt_num(v,1))
    cs['ticket_medio_ha'] = cs['ticket_medio_ha'].apply(fmt_brl)
    cs['rank'] = range(1, len(cs)+1)
    st.dataframe(cs[['rank','cliente','cidade','faturamento','liquido','hectares','ticket_medio_ha','num_vendas']]
                 .rename(columns={'rank':'#','cliente':'Cliente','cidade':'Cidade',
                                  'faturamento':'Faturamento','liquido':'Líquido',
                                  'hectares':'Hectares','ticket_medio_ha':'Ticket/ha','num_vendas':'Nº Vendas'}),
                 use_container_width=True, hide_index=True)

# ───────────────────────────────────────────────────────────────────
# ABA 3 — PRODUTOS
# ───────────────────────────────────────────────────────────────────
with tab_produtos:
    prod_df = df.groupby('produto').agg(
        faturamento=('valor_bruto','sum'), quantidade=('quantidade','sum'),
    ).sort_values('faturamento', ascending=False).reset_index()

    col_l, col_r = st.columns(2)
    with col_l:
        section("Top 15 Produtos por Faturamento")
        t15 = prod_df.head(15).sort_values('faturamento')
        fig = px.bar(t15, x='faturamento', y='produto', orientation='h',
                     color='faturamento', color_continuous_scale=['#C8E6C9','#1B5E20'],
                     text=t15['faturamento'].apply(fmt_brl))
        fig.update_traces(textposition='outside', textfont_size=11)
        layout_mobile(fig, 440, 10)
        fig.update_layout(showlegend=False, coloraxis_showscale=False,
                          xaxis=dict(showticklabels=False, showgrid=False), yaxis_title="", xaxis_title="")
        st.plotly_chart(fig, use_container_width=True)
    with col_r:
        section("Top 15 Produtos por Volume")
        t15q = prod_df.sort_values('quantidade', ascending=False).head(15).sort_values('quantidade')
        fig2 = px.bar(t15q, x='quantidade', y='produto', orientation='h',
                      color='quantidade', color_continuous_scale=['#B3E5FC','#01579B'],
                      text=t15q['quantidade'].apply(lambda v: fmt_num(v,1)))
        fig2.update_traces(textposition='outside', textfont_size=11)
        layout_mobile(fig2, 440, 10)
        fig2.update_layout(showlegend=False, coloraxis_showscale=False,
                           xaxis=dict(showticklabels=False, showgrid=False), yaxis_title="", xaxis_title="")
        st.plotly_chart(fig2, use_container_width=True)

    section("Detalhe — Corte de Silagem por Equipamento")
    sil = df[df['is_silagem']].groupby('produto').agg(
        hectares=('quantidade','sum'), faturamento=('valor_bruto','sum')
    ).reset_index()
    sil['receita_ha'] = sil['faturamento'] / sil['hectares']
    fig3 = make_subplots(rows=1, cols=2, subplot_titles=("Hectares Cortados","Receita por Hectare"))
    fig3.add_trace(go.Bar(x=sil['produto'], y=sil['hectares'], marker_color=VERDE_CLARO,
                          text=sil['hectares'].apply(lambda v: fmt_num(v,1)),
                          textposition='outside', name='ha'), row=1, col=1)
    fig3.add_trace(go.Bar(x=sil['produto'], y=sil['receita_ha'], marker_color=AMARELO,
                          text=sil['receita_ha'].apply(fmt_brl),
                          textposition='outside', name='R$/ha'), row=1, col=2)
    layout_mobile(fig3, 420, 100)
    fig3.update_layout(showlegend=False)
    fig3.update_xaxes(tickangle=35, tickfont=dict(size=10))
    st.plotly_chart(fig3, use_container_width=True)

# ───────────────────────────────────────────────────────────────────
# ABA 4 — CIDADES (tabela)
# ───────────────────────────────────────────────────────────────────
with tab_geo:
    n_cid = st.slider("Top N cidades", 5, 40, 20, key="top_cid")
    cid_df = df.groupby('cidade').agg(
        faturamento=('valor_bruto','sum'), clientes=('cliente','nunique'),
        hectares=('hectares','sum')
    ).sort_values('faturamento', ascending=False).reset_index()

    col_l, col_r = st.columns(2)
    with col_l:
        section("Faturamento por Cidade")
        tc = cid_df.head(n_cid).sort_values('faturamento')
        fig = px.bar(tc, x='faturamento', y='cidade', orientation='h',
                     color='faturamento', color_continuous_scale=['#A5D6A7','#1B5E20'],
                     text=tc['faturamento'].apply(fmt_brl))
        fig.update_traces(textposition='outside', textfont_size=11)
        layout_mobile(fig, max(380,n_cid*24), 10)
        fig.update_layout(showlegend=False, coloraxis_showscale=False,
                          xaxis=dict(showticklabels=False, showgrid=False), yaxis_title="", xaxis_title="")
        st.plotly_chart(fig, use_container_width=True)
    with col_r:
        section("Clientes por Cidade (Top 20)")
        tc2 = cid_df.sort_values('clientes', ascending=False).head(20).sort_values('clientes')
        fig2 = px.bar(tc2, x='clientes', y='cidade', orientation='h',
                      color='clientes', color_continuous_scale=['#B3E5FC','#01579B'],
                      text=tc2['clientes'])
        fig2.update_traces(textposition='outside', textfont_size=11)
        layout_mobile(fig2, 500, 10)
        fig2.update_layout(showlegend=False, coloraxis_showscale=False,
                           xaxis=dict(showticklabels=False, showgrid=False), yaxis_title="", xaxis_title="")
        st.plotly_chart(fig2, use_container_width=True)

    section("Tabela de Cidades")
    cs2 = cid_df.head(n_cid).copy()
    cs2['rank'] = range(1, len(cs2)+1)
    cs2['fat_fmt'] = cs2['faturamento'].apply(fmt_brl)
    cs2['ha_fmt']  = cs2['hectares'].apply(lambda v: fmt_num(v,1))
    cs2['rha']     = cs2.apply(lambda r: fmt_brl(r['faturamento']/r['hectares']) if r['hectares']>0 else '-', axis=1)
    st.dataframe(cs2[['rank','cidade','fat_fmt','clientes','ha_fmt','rha']]
                 .rename(columns={'rank':'#','cidade':'Cidade','fat_fmt':'Faturamento',
                                  'clientes':'Clientes','ha_fmt':'Hectares','rha':'Receita/ha'}),
                 use_container_width=True, hide_index=True)

# ───────────────────────────────────────────────────────────────────
# ABA 5 — MAPA GEOGRÁFICO
# ───────────────────────────────────────────────────────────────────
with tab_mapa:
    section("🗺️ Distribuição Geográfica das Cidades Atendidas")
    mapa_df = cid_df.copy()
    mapa_df['lat'] = mapa_df['cidade'].map(lambda c: CIDADES_COORDS.get(c, (None,None))[0])
    mapa_df['lon'] = mapa_df['cidade'].map(lambda c: CIDADES_COORDS.get(c, (None,None))[1])
    mapa_df = mapa_df.dropna(subset=['lat','lon'])
    mapa_df['faturamento_fmt'] = mapa_df['faturamento'].apply(fmt_brl)
    mapa_df['receita_ha'] = mapa_df.apply(
        lambda r: fmt_brl(r['faturamento']/r['hectares']) if r['hectares']>0 else '-', axis=1)

    st.caption(f"Exibindo {len(mapa_df)} de {len(cid_df)} cidades com coordenadas mapeadas")

    fig_map = px.scatter_mapbox(
        mapa_df, lat='lat', lon='lon', size='faturamento',
        color='faturamento', hover_name='cidade',
        hover_data={'faturamento_fmt': True, 'clientes': True, 'receita_ha': True,
                    'faturamento': False, 'lat': False, 'lon': False},
        color_continuous_scale='Greens', size_max=50,
        zoom=5.5, center={"lat":-28.5,"lon":-53.5},
        mapbox_style="open-street-map",
        labels={'faturamento_fmt':'Faturamento','clientes':'Clientes','receita_ha':'Receita/ha'}
    )
    fig_map.update_layout(
        height=550, margin=dict(l=0,r=0,t=0,b=0),
        coloraxis_colorbar_title="Faturamento (R$)",
        coloraxis_showscale=False
    )
    st.plotly_chart(fig_map, use_container_width=True)

    col_l, col_r = st.columns(2)
    with col_l:
        section("Top 10 Cidades — Faturamento")
        t10m = mapa_df.sort_values('faturamento', ascending=False).head(10)
        for _, r in t10m.iterrows():
            st.markdown(f"**{r['cidade']}** — {fmt_brl(r['faturamento'])} | {r['clientes']} clientes")
    with col_r:
        section("Top 10 Cidades — Receita/ha")
        mapa_df_ha = mapa_df[mapa_df['hectares']>0].copy()
        mapa_df_ha['rha_val'] = mapa_df_ha['faturamento'] / mapa_df_ha['hectares']
        t10h = mapa_df_ha.sort_values('rha_val', ascending=False).head(10)
        for _, r in t10h.iterrows():
            st.markdown(f"**{r['cidade']}** — {fmt_brl(r['rha_val'])}/ha | {fmt_num(r['hectares'],1)} ha")

# ───────────────────────────────────────────────────────────────────
# ABA 6 — EVOLUÇÃO MENSAL
# ───────────────────────────────────────────────────────────────────
with tab_temporal:
    mensal = (df.groupby('ano_mes').agg(
        faturamento=('valor_bruto','sum'), liquido=('valor_liquido','sum'),
        hectares=('hectares','sum'), vendas=('num_venda','nunique'),
        clientes=('cliente','nunique')
    ).reset_index().sort_values('ano_mes'))

    section("Evolução Mensal do Faturamento")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=mensal['ano_mes'], y=mensal['faturamento'],
                         name='Faturamento Bruto', marker_color=VERDE_CLARO, opacity=0.85))
    fig.add_trace(go.Scatter(x=mensal['ano_mes'], y=mensal['liquido'],
                             name='Receita Líquida', line=dict(color=AZUL, width=3),
                             mode='lines+markers', marker=dict(size=7)))
    layout_mobile(fig, 420, 80)
    fig.update_layout(barmode='overlay', xaxis_title="Mês/Ano", yaxis_title="R$")
    fig.update_xaxes(tickangle=45, tickfont=dict(size=10))
    st.plotly_chart(fig, use_container_width=True)

    col_l, col_r = st.columns(2)
    with col_l:
        section("Hectares Mensais")
        fig2 = px.area(mensal, x='ano_mes', y='hectares',
                       color_discrete_sequence=[VERDE_ESCURO],
                       labels={'hectares':'Hectares','ano_mes':''})
        layout_mobile(fig2, 320, 70)
        fig2.update_xaxes(tickangle=45, tickfont=dict(size=10))
        st.plotly_chart(fig2, use_container_width=True)
    with col_r:
        section("Clientes Ativos por Mês")
        fig3 = px.line(mensal, x='ano_mes', y='clientes',
                       color_discrete_sequence=[LARANJA], markers=True,
                       labels={'clientes':'Clientes Ativos','ano_mes':''})
        layout_mobile(fig3, 320, 70)
        fig3.update_xaxes(tickangle=45, tickfont=dict(size=10))
        st.plotly_chart(fig3, use_container_width=True)

# ───────────────────────────────────────────────────────────────────
# ABA 7 — SAFRAS + COMPARATIVO
# ───────────────────────────────────────────────────────────────────
with tab_safras:
    safra_df = (df[df['is_silagem']].groupby('safra').agg(
        hectares=('quantidade','sum'), faturamento=('valor_bruto','sum'),
        clientes=('cliente','nunique'), vendas=('num_venda','nunique')
    ).reset_index())
    safra_df['receita_ha'] = safra_df['faturamento'] / safra_df['hectares']
    safra_df['_o'] = safra_df['safra'].apply(lambda s: SAFRA_ORDER.index(s) if s in SAFRA_ORDER else 99)
    safra_df = safra_df.sort_values('_o').drop(columns='_o')
    safra_df_fil = safra_df[safra_df['safra'] != 'Outros Serviços']

    col_l, col_r = st.columns(2)
    with col_l:
        section("Hectares por Safra")
        fig = px.bar(safra_df_fil, x='safra', y='hectares', color='safra',
                     color_discrete_sequence=PALETTE,
                     text=safra_df_fil['hectares'].apply(lambda v: fmt_num(v,1)))
        fig.update_traces(textposition='outside', textfont_size=11)
        layout_mobile(fig, 420, 110)
        fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Hectares")
        fig.update_xaxes(tickangle=35, tickfont=dict(size=10))
        st.plotly_chart(fig, use_container_width=True)
    with col_r:
        section("Receita/ha por Safra")
        fig2 = px.bar(safra_df_fil, x='safra', y='receita_ha', color='safra',
                      color_discrete_sequence=PALETTE,
                      text=safra_df_fil['receita_ha'].apply(fmt_brl))
        fig2.update_traces(textposition='outside', textfont_size=11)
        layout_mobile(fig2, 420, 110)
        fig2.update_layout(showlegend=False, xaxis_title="", yaxis_title="R$/ha")
        fig2.update_xaxes(tickangle=35, tickfont=dict(size=10))
        st.plotly_chart(fig2, use_container_width=True)

    # Comparativo entre safras consecutivas
    section("📊 Comparativo entre Safras")
    if len(safra_df_fil) >= 2:
        safras_list = safra_df_fil['safra'].tolist()
        col_a, col_b = st.columns(2)
        with col_a: s1 = st.selectbox("Safra A", safras_list, index=0)
        with col_b: s2 = st.selectbox("Safra B", safras_list, index=min(1,len(safras_list)-1))
        r1 = safra_df_fil[safra_df_fil['safra']==s1].iloc[0]
        r2 = safra_df_fil[safra_df_fil['safra']==s2].iloc[0]
        comp_data = pd.DataFrame({
            'Indicador':['Hectares','Faturamento (R$)','Receita/ha (R$)','Clientes','Nº Vendas'],
            s1:[fmt_num(r1['hectares'],1), fmt_brl(r1['faturamento']),
                fmt_brl(r1['receita_ha']), str(int(r1['clientes'])), str(int(r1['vendas']))],
            s2:[fmt_num(r2['hectares'],1), fmt_brl(r2['faturamento']),
                fmt_brl(r2['receita_ha']), str(int(r2['clientes'])), str(int(r2['vendas']))],
        })
        # Variação %
        variacoes = []
        for val1, val2 in [(r1['hectares'],r2['hectares']),(r1['faturamento'],r2['faturamento']),
                           (r1['receita_ha'],r2['receita_ha']),(r1['clientes'],r2['clientes']),
                           (r1['vendas'],r2['vendas'])]:
            if val1 > 0:
                pct = (val2 - val1) / val1 * 100
                variacoes.append(f"{'▲' if pct>=0 else '▼'} {abs(pct):.1f}%")
            else: variacoes.append("—")
        comp_data['Variação'] = variacoes
        st.dataframe(comp_data, use_container_width=True, hide_index=True)

        # Radar chart
        cats = ['Hectares','Faturamento','Receita/ha','Clientes']
        vals1 = [r1['hectares'], r1['faturamento']/1e6, r1['receita_ha']/1000, r1['clientes']]
        vals2 = [r2['hectares'], r2['faturamento']/1e6, r2['receita_ha']/1000, r2['clientes']]
        mx = [max(a,b,0.001) for a,b in zip(vals1,vals2)]
        n1 = [v/m for v,m in zip(vals1,mx)]
        n2 = [v/m for v,m in zip(vals2,mx)]
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(r=n1+[n1[0]], theta=cats+[cats[0]], fill='toself',
                                             name=s1, line=dict(color=VERDE_CLARO)))
        fig_radar.add_trace(go.Scatterpolar(r=n2+[n2[0]], theta=cats+[cats[0]], fill='toself',
                                             name=s2, line=dict(color=AZUL), opacity=0.7))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0,1])),
                                 height=380, margin=dict(l=40,r=40,t=40,b=40),
                                 legend=dict(orientation='h',y=-0.1))
        st.plotly_chart(fig_radar, use_container_width=True)

    section("Resumo por Safra")
    ss = safra_df.copy()
    ss['faturamento'] = ss['faturamento'].apply(fmt_brl)
    ss['hectares']    = ss['hectares'].apply(lambda v: fmt_num(v,1))
    ss['receita_ha']  = ss['receita_ha'].apply(fmt_brl)
    st.dataframe(ss[['safra','hectares','faturamento','receita_ha','clientes','vendas']]
                 .rename(columns={'safra':'Safra','hectares':'Hectares','faturamento':'Faturamento',
                                  'receita_ha':'Receita/ha','clientes':'Clientes','vendas':'Nº Vendas'}),
                 use_container_width=True, hide_index=True)

# ───────────────────────────────────────────────────────────────────
# ABA 8 — SAZONALIDADE
# ───────────────────────────────────────────────────────────────────
with tab_sazonalidade:
    section("📅 Heatmap de Sazonalidade — Faturamento por Mês e Ano")
    meses_pt = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
    saz = df.groupby(['ano','mes'])['valor_bruto'].sum().reset_index()
    saz_pivot = saz.pivot(index='ano', columns='mes', values='valor_bruto').fillna(0)
    saz_pivot.columns = [meses_pt[m-1] for m in saz_pivot.columns]

    fig_heat = px.imshow(
        saz_pivot, color_continuous_scale='Greens', aspect='auto',
        labels={'x':'Mês','y':'Ano','color':'Faturamento (R$)'},
        text_auto=False,
    )
    # Adicionar texto com valor
    for i, ano in enumerate(saz_pivot.index):
        for j, mes in enumerate(saz_pivot.columns):
            val = saz_pivot.loc[ano, mes]
            if val > 0:
                fig_heat.add_annotation(x=j, y=i, text=fmt_brl(val).replace("R$ ",""),
                                        showarrow=False, font=dict(size=10, color='white' if val > saz_pivot.values.max()*0.5 else '#1B5E20'))
    layout_mobile(fig_heat, 340, 40)
    fig_heat.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig_heat, use_container_width=True)

    section("Hectares por Mês e Ano")
    saz_ha = df[df['is_silagem']].groupby(['ano','mes'])['hectares'].sum().reset_index()
    saz_ha_pivot = saz_ha.pivot(index='ano', columns='mes', values='hectares').fillna(0)
    saz_ha_pivot.columns = [meses_pt[m-1] for m in saz_ha_pivot.columns]
    fig_heat2 = px.imshow(saz_ha_pivot, color_continuous_scale='YlGn', aspect='auto',
                           labels={'x':'Mês','y':'Ano','color':'Hectares'})
    layout_mobile(fig_heat2, 320, 40)
    fig_heat2.update_layout(coloraxis_showscale=True, coloraxis_colorbar_title="ha")
    st.plotly_chart(fig_heat2, use_container_width=True)

    section("Meses com Maior Faturamento (histórico)")
    saz_mes = df.groupby('mes')['valor_bruto'].sum().reset_index()
    saz_mes['mes_nome'] = saz_mes['mes'].apply(lambda m: meses_pt[m-1])
    fig_mes = px.bar(saz_mes, x='mes_nome', y='valor_bruto',
                     color='valor_bruto', color_continuous_scale='Greens',
                     text=saz_mes['valor_bruto'].apply(fmt_brl))
    fig_mes.update_traces(textposition='outside', textfont_size=11)
    layout_mobile(fig_mes, 340, 40)
    fig_mes.update_layout(showlegend=False, coloraxis_showscale=False,
                          xaxis_title="Mês", yaxis_title="R$")
    st.plotly_chart(fig_mes, use_container_width=True)

# ───────────────────────────────────────────────────────────────────
# ABA 9 — FIDELIDADE
# ───────────────────────────────────────────────────────────────────
with tab_fidelidade:
    section("🔄 Análise de Fidelidade de Clientes")
    fid = df[df['is_silagem']].groupby('cliente')['safra'].nunique().reset_index()
    fid.columns = ['cliente','num_safras']
    fid_fat = df.groupby('cliente')['valor_bruto'].sum().reset_index()
    fid_fat.columns = ['cliente','faturamento']
    fid = fid.merge(fid_fat, on='cliente')
    fid['categoria_fidelidade'] = fid['num_safras'].apply(
        lambda n: '⭐ Fiel (4+ safras)' if n >= 4 else
                  '🔄 Recorrente (2-3)' if n >= 2 else '1ª vez (1 safra)')

    col_l, col_r = st.columns(2)
    with col_l:
        section("Distribuição de Fidelidade")
        fid_grupo = fid.groupby('categoria_fidelidade').agg(
            clientes=('cliente','count'), faturamento=('faturamento','sum')).reset_index()
        fig = px.pie(fid_grupo, values='clientes', names='categoria_fidelidade',
                     color_discrete_sequence=[VERDE_CLARO, AZUL, LARANJA], hole=0.4)
        fig.update_traces(textinfo='label+percent+value', textfont_size=12)
        layout_mobile(fig, 340, 20)
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with col_r:
        section("Faturamento por Nível de Fidelidade")
        fig2 = px.bar(fid_grupo, x='categoria_fidelidade', y='faturamento',
                      color='categoria_fidelidade',
                      color_discrete_sequence=[VERDE_CLARO, AZUL, LARANJA],
                      text=fid_grupo['faturamento'].apply(fmt_brl))
        fig2.update_traces(textposition='outside', textfont_size=11)
        layout_mobile(fig2, 340, 60)
        fig2.update_layout(showlegend=False, xaxis_title="", yaxis_title="R$")
        st.plotly_chart(fig2, use_container_width=True)

    section("Clientes Fiéis (4+ safras)")
    fieis = fid[fid['num_safras']>=4].sort_values('faturamento', ascending=False)
    if len(fieis) > 0:
        fieis_show = fieis.copy()
        fieis_show['faturamento'] = fieis_show['faturamento'].apply(fmt_brl)
        st.dataframe(fieis_show[['cliente','num_safras','faturamento']]
                     .rename(columns={'cliente':'Cliente','num_safras':'Safras','faturamento':'Faturamento'}),
                     use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum cliente com 4 ou mais safras no período filtrado.")

    section("Clientes de Primeira Vez (potencial de retorno)")
    novos = fid[fid['num_safras']==1].sort_values('faturamento', ascending=False).head(20)
    novos_show = novos.copy()
    novos_show['faturamento'] = novos_show['faturamento'].apply(fmt_brl)
    st.dataframe(novos_show[['cliente','faturamento']]
                 .rename(columns={'cliente':'Cliente','faturamento':'Faturamento'}),
                 use_container_width=True, hide_index=True)
    st.caption(f"Total de {len(fid[fid['num_safras']==1])} clientes contrataram apenas uma vez — oportunidade de fidelização.")

# ───────────────────────────────────────────────────────────────────
# ABA 10 — PROJEÇÃO
# ───────────────────────────────────────────────────────────────────
with tab_projecao:
    section("🎯 Projeção da Próxima Safra")
    st.info("Projeção baseada na média das últimas 3 safras por cliente, extrapolando tendência de crescimento/queda.")

    safras_ord = [s for s in SAFRA_ORDER if s in df['safra'].unique() and s != 'Outros Serviços']

    if len(safras_ord) >= 2:
        ultimas3 = safras_ord[-3:]
        proj_cli = []
        for cli in df[df['is_silagem']]['cliente'].unique():
            registros = []
            for s in ultimas3:
                sub = df[(df['cliente']==cli) & (df['safra']==s) & df['is_silagem']]
                if len(sub) > 0:
                    registros.append({'safra':s,'ha':sub['quantidade'].sum(),'fat':sub['valor_bruto'].sum()})
            if len(registros) >= 2:
                ha_vals  = [r['ha']  for r in registros]
                fat_vals = [r['fat'] for r in registros]
                proj_ha  = np.mean(ha_vals) * (1 + (ha_vals[-1]-ha_vals[0])/(ha_vals[0]*max(len(ha_vals)-1,1)) * 0.5) if ha_vals[0]>0 else np.mean(ha_vals)
                proj_fat = np.mean(fat_vals) * (1 + (fat_vals[-1]-fat_vals[0])/(fat_vals[0]*max(len(fat_vals)-1,1)) * 0.5) if fat_vals[0]>0 else np.mean(fat_vals)
                proj_cli.append({'cliente':cli,'ha_proj':max(proj_ha,0),'fat_proj':max(proj_fat,0),
                                 'safras_base':len(registros),'tendencia': '▲' if ha_vals[-1]>ha_vals[0] else '▼'})

        if proj_cli:
            proj_df = pd.DataFrame(proj_cli).sort_values('fat_proj', ascending=False)
            total_ha_proj  = proj_df['ha_proj'].sum()
            total_fat_proj = proj_df['fat_proj'].sum()

            col1, col2, col3 = st.columns(3)
            with col1: st.metric("Hectares Projetados",    fmt_num(total_ha_proj,1)+" ha",
                                  delta=f"{((total_ha_proj/total_ha-1)*100):+.1f}% vs atual" if total_ha>0 else "")
            with col2: st.metric("Faturamento Projetado",  fmt_brl(total_fat_proj),
                                  delta=f"{((total_fat_proj/fat_total-1)*100):+.1f}% vs atual" if fat_total>0 else "")
            with col3: st.metric("Clientes na Projeção",   str(len(proj_df)),
                                  delta=f"baseado nas safras: {', '.join(ultimas3[-2:])}")

            section(f"Top 20 Clientes — Projeção (base: {', '.join(ultimas3)})")
            proj_show = proj_df.head(20).copy()
            fig = px.bar(proj_show.sort_values('ha_proj'), x='ha_proj', y='cliente',
                         orientation='h', color='fat_proj',
                         color_continuous_scale='Greens',
                         text=proj_show.sort_values('ha_proj')['ha_proj'].apply(lambda v: fmt_num(v,1)+" ha"))
            fig.update_traces(textposition='outside', textfont_size=11)
            layout_mobile(fig, max(400, len(proj_show)*24), 10)
            fig.update_layout(coloraxis_colorbar_title="Fat. Proj. (R$)",
                              xaxis_title="Hectares Projetados", yaxis_title="")
            st.plotly_chart(fig, use_container_width=True)

            proj_show['ha_proj']  = proj_show['ha_proj'].apply(lambda v: fmt_num(v,1))
            proj_show['fat_proj'] = proj_show['fat_proj'].apply(fmt_brl)
            st.dataframe(proj_show[['cliente','tendencia','safras_base','ha_proj','fat_proj']]
                         .rename(columns={'cliente':'Cliente','tendencia':'Tendência',
                                          'safras_base':'Safras Analisadas',
                                          'ha_proj':'Hectares Projetados','fat_proj':'Faturamento Projetado'}),
                         use_container_width=True, hide_index=True)
        else:
            st.warning("Dados insuficientes para projeção com os filtros atuais.")
    else:
        st.warning("São necessárias pelo menos 2 safras para gerar projeção.")

# ───────────────────────────────────────────────────────────────────
# ABA 11 — DADOS
# ───────────────────────────────────────────────────────────────────
with tab_dados:
    section("Dados Filtrados")
    col_s, col_e, col_x = st.columns([3,1,1])
    with col_s:
        search = st.text_input("🔍 Buscar", placeholder="Cliente, cidade, produto, safra...")
    with col_e:
        st.markdown("<br>", unsafe_allow_html=True)
        csv_data = df.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig')
        st.download_button("⬇️ CSV", data=csv_data, file_name="agrosilagem_dados.csv", mime="text/csv")
    with col_x:
        st.markdown("<br>", unsafe_allow_html=True)
        # Exportação Excel
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            exp = df[['num_venda','data_venda','cliente','cidade','categoria','produto',
                       'safra','quantidade','hectares','valor_bruto','valor_liquido']].copy()
            exp['data_venda'] = exp['data_venda'].dt.strftime('%d/%m/%Y')
            exp.columns = ['Nº Venda','Data','Cliente','Cidade','Categoria','Produto',
                           'Safra','Qtd','Hectares','Valor Bruto','Valor Líquido']
            exp.to_excel(writer, index=False, sheet_name='Vendas')
            cli_df.to_excel(writer, index=False, sheet_name='Clientes')
        buf.seek(0)
        st.download_button("⬇️ Excel", data=buf, file_name="agrosilagem_dados.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    show_df = df.copy()
    if search:
        mask = (show_df['cliente'].str.contains(search,case=False,na=False) |
                show_df['cidade'].str.contains(search,case=False,na=False) |
                show_df['produto'].str.contains(search,case=False,na=False) |
                show_df['safra'].str.contains(search,case=False,na=False))
        show_df = show_df[mask]

    show_fmt = show_df[['num_venda','data_venda','cliente','cidade','categoria',
                         'produto','safra','quantidade','hectares','valor_bruto','valor_liquido']].copy()
    show_fmt['data_venda']    = show_fmt['data_venda'].dt.strftime('%d/%m/%Y')
    show_fmt['valor_bruto']   = show_fmt['valor_bruto'].apply(fmt_brl)
    show_fmt['valor_liquido'] = show_fmt['valor_liquido'].apply(fmt_brl)
    show_fmt['quantidade']    = show_fmt['quantidade'].apply(lambda v: fmt_num(v,2))
    show_fmt['hectares']      = show_fmt['hectares'].apply(lambda v: fmt_num(v,2) if v>0 else '-')
    show_fmt.columns = ['Nº Venda','Data','Cliente','Cidade','Categoria',
                        'Produto','Safra','Qtd','Hectares','Valor Bruto','Valor Líquido']
    st.caption(f"Exibindo {len(show_fmt):,} de {len(df):,} registros filtrados")
    st.dataframe(show_fmt, use_container_width=True, hide_index=True, height=500)

# ───────────────────────────────────────────────────────────────────
# ABA 12 — INSIGHTS
# ───────────────────────────────────────────────────────────────────
with tab_insights:
    section("💡 Insights Automáticos")
    mensal2 = df.groupby('ano_mes').agg(faturamento=('valor_bruto','sum'),vendas=('num_venda','nunique')).reset_index().sort_values('ano_mes')
    melhor_mes = mensal2.sort_values('faturamento',ascending=False).iloc[0] if len(mensal2)>0 else None
    cresc = 0
    if len(mensal2) >= 2:
        ult, pen = mensal2.iloc[-1]['faturamento'], mensal2.iloc[-2]['faturamento']
        cresc = (ult-pen)/pen*100 if pen>0 else 0
    sil_eq = df[df['is_silagem']].groupby('produto').agg(ha=('quantidade','sum'),fat=('valor_bruto','sum')).reset_index()
    sil_eq['rha'] = sil_eq['fat']/sil_eq['ha']

    def ins(texto, cls=""):
        return f'<div class="insight-box {cls}">{texto}</div>'

    items = []
    top1 = cli_df.iloc[0] if len(cli_df)>0 else None
    if top1 is not None:
        items.append(ins(f"🏆 <b>Maior cliente:</b> <b>{top1['cliente']}</b> ({top1['cidade']}) — {fmt_brl(top1['faturamento'])} | {top1['hectares']:.0f} ha"))
    items.append(ins(f"📊 <b>Concentração:</b> Top 5 clientes = <b>{conc5_pct:.1f}%</b> do faturamento ({fmt_brl(fat_top5)})",
                     cls="alerta" if conc5_pct>60 else ""))
    if melhor_mes is not None:
        items.append(ins(f"📅 <b>Melhor mês:</b> <b>{melhor_mes['ano_mes']}</b> — {fmt_brl(melhor_mes['faturamento'])} ({melhor_mes['vendas']:.0f} vendas)"))
    if abs(cresc)>0:
        items.append(ins(f"{'📈' if cresc>0 else '📉'} <b>Variação último mês:</b> <b>{cresc:+.1f}%</b> vs mês anterior", cls="" if cresc>0 else "alerta"))
    if len(sil_eq)>0:
        be = sil_eq.sort_values('rha',ascending=False).iloc[0]
        items.append(ins(f"🚜 <b>Equipamento mais rentável:</b> <b>{be['produto']}</b> — {fmt_brl(be['rha'])}/ha ({fmt_num(be['ha'],1)} ha)"))

    # Fidelidade insights
    if len(fid_grupo)>0:
        n_fieis  = fid[fid['num_safras']>=4]['cliente'].count() if 'fid' in dir() else 0
        n_novos  = fid[fid['num_safras']==1]['cliente'].count() if 'fid' in dir() else 0
        if n_fieis > 0:
            items.append(ins(f"⭐ <b>Clientes fiéis:</b> {n_fieis} clientes com 4+ safras consecutivas"))
        if n_novos > 0:
            items.append(ins(f"🎯 <b>Potencial de fidelização:</b> {n_novos} clientes de primeira vez — oportunidade de recorrência", cls="alerta"))

    cid_ha = cid_df[cid_df['hectares']>0].sort_values('hectares',ascending=False)
    if len(cid_ha)>0:
        tc = cid_ha.iloc[0]
        items.append(ins(f"📍 <b>Maior volume de hectares:</b> <b>{tc['cidade']}</b> — {fmt_num(tc['hectares'],1)} ha | {fmt_brl(tc['faturamento'])}"))

    for item in items:
        st.markdown(item, unsafe_allow_html=True)

# ───────────────────────────────────────────────────────────────────
# ABA 13 — RESUMO EXECUTIVO
# ───────────────────────────────────────────────────────────────────
with tab_resumo:
    section("📄 Resumo Executivo")
    st.markdown(f"""
### AGROSILAGEM — Relatório Executivo
**Período:** {dt_inicio.strftime('%d/%m/%Y')} a {dt_fim.strftime('%d/%m/%Y')}
**Gerado em:** {datetime.now().strftime('%d/%m/%Y às %H:%M')}

---
#### Indicadores Financeiros

| Indicador | Valor |
|-----------|-------|
| **Faturamento Bruto Total** | {fmt_brl(fat_total)} |
| **Receita Líquida Total** | {fmt_brl(liq_total)} |
| **Margem Bruta** | {(liq_total/fat_total*100 if fat_total>0 else 0):.1f}% |
| **Ticket Médio por Hectare** | {fmt_brl(ticket_medio)} |
| **Receita Média por Hectare** | {fmt_brl(rec_ha)} |

#### Volume Operacional

| Indicador | Valor |
|-----------|-------|
| **Total de Hectares Cortados** | {fmt_num(total_ha,1)} ha |
| **Total de Clientes Ativos** | {total_cli} |
| **Total de Vendas Realizadas** | {num_vendas} |
| **Cidades Atendidas** | {df['cidade'].nunique()} |

#### Concentração de Carteira

| Indicador | Valor | Status |
|-----------|-------|--------|
| **Top 5 clientes** | {conc5_pct:.1f}% do faturamento | {'⚠️ Alto' if conc5_pct>60 else '✅ Saudável'} |
| **Top 10 clientes** | {(fat_top10/fat_total*100 if fat_total>0 else 0):.1f}% do faturamento | — |

#### Top 5 Clientes
""")
    for i, (_, r) in enumerate(cli_df.head(5).iterrows(), 1):
        st.markdown(f"{i}. **{r['cliente']}** ({r['cidade']}) — {fmt_brl(r['faturamento'])} | {fmt_num(r['hectares'],1)} ha")

    st.markdown("---")
    # Mini gráficos de resumo
    col_l, col_r = st.columns(2)
    with col_l:
        section("Faturamento Mensal")
        fig = px.area(mensal2, x='ano_mes', y='faturamento',
                      color_discrete_sequence=[VERDE_CLARO])
        layout_mobile(fig, 260, 60, 11)
        fig.update_xaxes(tickangle=45, tickfont=dict(size=9))
        fig.update_layout(xaxis_title="", yaxis_title="R$", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with col_r:
        section("Top 10 Clientes")
        top10r = cli_df.head(10).sort_values('faturamento')
        fig2 = px.bar(top10r, x='faturamento', y='cliente', orientation='h',
                      color='faturamento', color_continuous_scale=['#A5D6A7','#1B5E20'])
        layout_mobile(fig2, 260, 10, 10)
        fig2.update_layout(showlegend=False, coloraxis_showscale=False,
                           xaxis=dict(showticklabels=False), yaxis_title="", xaxis_title="")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.caption(f"Agrosilagem © 2024–2026 | Dashboard gerado automaticamente | Base: {len(df_raw):,} registros")
