"""
CRM — Mapa de Clientes
Damiani Agrosilagem
"""
import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from database import clientes_com_coords, listar_clientes

st.set_page_config(
    page_title="Mapa — Damiani Agrosilagem",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
[data-testid="stSidebar"] { background-color: #1B5E20; border-right: none; }
[data-testid="stSidebar"] * { color: #FFFFFF !important; }
[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] [data-baseweb="input"] input {
    background-color: #FFFFFF !important; color: #1A2E1A !important;
}
.block-container { padding-top: 2rem !important; }
</style>
""", unsafe_allow_html=True)

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="background:rgba(0,0,0,.25);border-radius:10px;padding:14px 16px;
    text-align:center;border:1px solid rgba(255,255,255,.15);margin-bottom:12px;">
    <h2 style="color:#fff;margin:0;font-size:1.1rem;font-weight:700;">
    🌾 Damiani Agrosilagem</h2>
    <p style="color:rgba(255,255,255,.7);margin:3px 0 0;font-size:.71rem;">
    CRM Comercial</p></div>
    """, unsafe_allow_html=True)

    st.page_link("app.py", label="📊 Dashboard", icon=None)
    st.page_link("pages/1_🗂️_Clientes.py", label="🗂️ Clientes", icon=None)
    st.page_link("pages/2_🗺️_Mapa.py", label="🗺️ Mapa", icon=None)

    st.markdown("---")
    st.markdown('<div style="background:rgba(255,255,255,.12);border-left:3px solid #81C784;'
                'border-radius:0 6px 6px 0;padding:5px 10px;margin:8px 0;">'
                '<span style="color:#fff;font-weight:700;font-size:.75rem;'
                'text-transform:uppercase;">🔍 Filtros</span></div>', unsafe_allow_html=True)

    filtro_class = st.multiselect("Classificação", ["A", "B", "C"], default=["A", "B", "C"])
    usar_cluster = st.checkbox("Agrupar marcadores", value=True)

# ─── DADOS ───────────────────────────────────────────────────────────────────
st.title("🗺️ Mapa de Clientes")

df_coords = clientes_com_coords()
df_todos = listar_clientes()

n_total = len(df_todos)
n_com_coords = len(df_coords)
n_sem_coords = n_total - n_com_coords

col1, col2, col3 = st.columns(3)
col1.metric("Total de Clientes", n_total)
col2.metric("No Mapa", n_com_coords)
col3.metric("Sem Coordenadas", n_sem_coords,
            help="Configure as coordenadas na ficha do cliente ou selecione uma cidade da lista.")

if n_sem_coords > 0:
    st.info(
        f"ℹ️ **{n_sem_coords} cliente(s) sem coordenadas** não aparecem no mapa. "
        "Acesse a ficha de cada cliente em 🗂️ Clientes e selecione a cidade para geocodificar automaticamente."
    )

if df_coords.empty:
    st.warning("Nenhum cliente com coordenadas cadastradas ainda. Importe os clientes e as coordenadas serão preenchidas automaticamente pelas cidades conhecidas.")
    st.stop()

# ─── Filtra por classificação ─────────────────────────────────────────────────
if filtro_class:
    df_coords = df_coords[df_coords["classificacao"].isin(filtro_class)]

if df_coords.empty:
    st.info("Nenhum cliente com essa classificação possui coordenadas.")
    st.stop()

# ─── Mapa ─────────────────────────────────────────────────────────────────────
CORES = {"A": "green", "B": "blue", "C": "orange"}

centro_lat = df_coords["lat"].mean()
centro_lng = df_coords["lng"].mean()

mapa = folium.Map(
    location=[centro_lat, centro_lng],
    zoom_start=7,
    tiles="CartoDB positron",
)

layer = MarkerCluster() if usar_cluster else mapa

for _, row in df_coords.iterrows():
    cor = CORES.get(row.get("classificacao", "B"), "blue")

    popup_html = f"""
    <div style="font-family:sans-serif;min-width:160px">
        <b style="font-size:1rem">{row['nome']}</b><br>
        <span style="background:{'#1B5E20' if cor=='green' else '#1565C0' if cor=='blue' else '#E65100'};
        color:#fff;padding:2px 8px;border-radius:8px;font-size:.75rem">
        {row.get('classificacao','B')}</span><br><br>
        📍 {row.get('cidade','')}, {row.get('estado','')}<br>
        {'📞 ' + row['telefone'] + '<br>' if row.get('telefone') else ''}
        {'👤 ' + row['responsavel'] if row.get('responsavel') else ''}
    </div>
    """

    marker = folium.Marker(
        location=[row["lat"], row["lng"]],
        popup=folium.Popup(popup_html, max_width=220),
        tooltip=row["nome"],
        icon=folium.Icon(color=cor, icon="leaf", prefix="fa"),
    )

    if usar_cluster:
        marker.add_to(layer)
    else:
        marker.add_to(mapa)

if usar_cluster:
    layer.add_to(mapa)

# Legenda
legenda_html = """
<div style="position:fixed;bottom:30px;left:30px;background:white;padding:12px 16px;
border-radius:10px;border:1px solid #ccc;font-family:sans-serif;font-size:.82rem;z-index:1000">
<b>Classificação</b><br>
<span style="color:#2E7D32">● A</span> — Prioritário<br>
<span style="color:#1565C0">● B</span> — Regular<br>
<span style="color:#E65100">● C</span> — Baixo volume
</div>
"""
mapa.get_root().html.add_child(folium.Element(legenda_html))

# Renderiza mapa
st_folium(mapa, width="100%", height=580, returned_objects=[])

# ─── Tabela abaixo do mapa ────────────────────────────────────────────────────
with st.expander("📋 Lista dos clientes no mapa", expanded=False):
    cols_show = [c for c in ["nome", "cidade", "estado", "classificacao", "responsavel", "telefone"]
                 if c in df_coords.columns]
    st.dataframe(
        df_coords[cols_show].rename(columns=lambda c: c.replace("_"," ").title()),
        use_container_width=True,
        hide_index=True,
    )
