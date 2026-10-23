"""
Central de Relatórios — todos os relatórios num lugar só
Damiani Agrosilagem
"""
import io

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as stc

from base_vendas import (fmt_brl, fmt_num, carregar_vendas, versao_base, preparar_itens,
                         load_horas, horas_por_ha, HORAS_FILE)
from tabela_excel import tabela_excel
from relatorios import relatorio_cliente, relatorio_safra, relatorio_anual

st.set_page_config(
    page_title="Relatórios — Damiani Agrosilagem",
    page_icon="📑",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
[data-testid="stSidebar"] { background-color: #1B5E20; border-right: none; }
[data-testid="stSidebar"] * { color: #FFFFFF !important; }
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] p { font-size: .95rem; }
.block-container { padding-top: 2rem !important; }
.rel-titulo { font-size: 1.6rem !important; font-weight: 700; color: #1B5E20; margin: 0; line-height: 1.3; }
.rel-sub { color: #5E6658; margin: 2px 0 18px; font-size: .92rem; }
.rel-grupo { font-size: .78rem; font-weight: 700; letter-spacing: .06em; text-transform: uppercase;
             color: #5E6658; margin: 14px 0 6px; }
/* Cada tipo de relatório é um card clicável, preenchido */
[class*="st-key-tipo_"] button {
    border: none !important; border-radius: 12px !important; color: #FFFFFF !important;
    min-height: 96px; padding: 14px 16px !important; justify-content: flex-start; text-align: left;
    box-shadow: 0 2px 6px rgba(0,0,0,0.12); transition: filter .15s ease, transform .15s ease;
}
[class*="st-key-tipo_"] button:hover { filter: brightness(1.08); transform: translateY(-1px); }
[class*="st-key-tipo_"] button p { white-space: pre-line; text-align: left; font-size: .85rem; line-height: 1.4; color: #FFFFFF; }
[class*="st-key-tipo_"] button p strong { display: block; font-size: 1.08rem; margin-bottom: 2px; }
.st-key-tipo_cliente button, .st-key-tipo_servico button, .st-key-tipo_detalhe button { background: #2E6B2A !important; }
.st-key-tipo_pdf_cliente button, .st-key-tipo_pdf_safra button, .st-key-tipo_pdf_ano button { background: #1F5C6B !important; }
.st-key-tipo_resumo button, .st-key-tipo_exportar button { background: #5B6B23 !important; }
</style>
""", unsafe_allow_html=True)

# Página em português: evita que o tradutor do Chrome duplique textos
stc.html("""<script>try{const h=window.parent.document.documentElement;h.setAttribute('lang','pt-BR');
h.setAttribute('translate','no');h.classList.add('notranslate');}catch(e){}</script>""", height=0)

with st.sidebar:
    st.page_link("app.py", label="📊 Dashboard")
    st.page_link("pages/3_📑_Relatorios.py", label="📑 Relatórios")
    st.page_link("pages/1_🗂️_Clientes.py", label="🗂️ Clientes CRM")
    st.page_link("pages/2_🗺️_Mapa.py", label="🗺️ Mapa")

df_raw = carregar_vendas(versao_base())
if df_raw is None:
    st.error("Base de dados não encontrada. Importe o arquivo do Conta Azul no Dashboard.")
    st.stop()

# ─── Catálogo de relatórios ──────────────────────────────────────────────────
TIPOS = {
    "cliente":     ("Por cliente", "Hectares, valor por ha, valor total e horas p/ ha de cada cliente"),
    "servico":     ("Por serviço / equipamento", "Quantidade, valor unitário médio e total de cada máquina"),
    "detalhe":     ("Detalhado", "Cada item de venda, com quantidade, valor unitário e total"),
    "pdf_cliente": ("PDF do cliente", "Histórico completo de um cliente, pronto para enviar"),
    "pdf_safra":   ("PDF da safra", "Resultado de uma safra: clientes, hectares e faturamento"),
    "pdf_ano":     ("PDF do ano agrícola", "Ano agrícola (dez–nov) comparado com o anterior"),
    "resumo":      ("Resumo executivo", "Principais números, maiores clientes e evolução mensal"),
    "exportar":    ("Exportar base completa", "Todas as vendas em Excel ou CSV"),
}
GRUPOS = [
    ("Tabelas com filtros", ["cliente", "servico", "detalhe"]),
    ("Relatórios em PDF", ["pdf_cliente", "pdf_safra", "pdf_ano"]),
    ("Visão geral e exportação", ["resumo", "exportar"]),
]

tipo = st.session_state.get("rel_tipo")


def abrir(t):
    st.session_state["rel_tipo"] = t


if tipo not in TIPOS:
    st.markdown('<div class="rel-titulo">📑 Central de Relatórios</div>'
                '<p class="rel-sub">Escolha o relatório. Os filtros de período, safra, cidade e cliente '
                'aparecem dentro de cada um.</p>', unsafe_allow_html=True)
    for grupo, chaves in GRUPOS:
        st.markdown(f'<p class="rel-grupo">{grupo}</p>', unsafe_allow_html=True)
        for col, k in zip(st.columns(3), chaves):
            nome, desc = TIPOS[k]
            col.button(f"**{nome}**\n{desc}", key=f"tipo_{k}", on_click=abrir, args=(k,), use_container_width=True)
    st.stop()

# ─── Relatório aberto ────────────────────────────────────────────────────────
nome, desc = TIPOS[tipo]
st.button("← Todos os relatórios", on_click=abrir, args=(None,), type="tertiary")
st.markdown(f'<div class="rel-titulo">{nome}</div><p class="rel-sub">{desc}</p>', unsafe_allow_html=True)


def filtros(rel):
    """Período, safra, cidade, cliente e categoria — no topo do relatório."""
    d0, d1 = rel['data_venda'].min().date(), rel['data_venda'].max().date()
    c1, c2, c3, c4, c5 = st.columns([1.3, 1, 1, 1, 1])
    per = c1.date_input("Período", value=(d0, d1), min_value=d0, max_value=d1, format="DD/MM/YYYY", key="f_periodo")
    safras = c2.multiselect("Safra", sorted(rel['safra_venda'].unique()), placeholder="Todas", key="f_safra")
    cidades = c3.multiselect("Cidade", sorted(rel['cidade'].dropna().unique()), placeholder="Todas", key="f_cidade")
    base_cli = rel[rel['cidade'].isin(cidades)] if cidades else rel
    clientes = c4.multiselect("Cliente", sorted(base_cli['cliente'].dropna().unique()), placeholder="Todos", key="f_cliente")
    cats = c5.multiselect("Categoria", sorted(rel['categoria'].dropna().unique()), placeholder="Todas", key="f_cat")
    if isinstance(per, (list, tuple)) and len(per) == 2:
        rel = rel[rel['data_venda'].dt.date.between(per[0], per[1])]
    if safras:   rel = rel[rel['safra_venda'].isin(safras)]
    if cidades:  rel = rel[rel['cidade'].isin(cidades)]
    if clientes: rel = rel[rel['cliente'].isin(clientes)]
    if cats:     rel = rel[rel['categoria'].isin(cats)]
    return rel


def baixar(tabela, nome_arquivo, aba):
    """Botões Excel (com autofiltro) e CSV do que está na tela."""
    d1, d2, _ = st.columns([1, 1, 4])
    aba = "".join("-" if ch in '\\/*?:[]' else ch for ch in aba)  # caracteres que o Excel não aceita no nome da aba
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl', datetime_format='DD/MM/YYYY') as writer:
        tabela.to_excel(writer, index=False, sheet_name=aba[:31])
        ws = writer.sheets[aba[:31]]
        ws.auto_filter.ref = ws.dimensions
        ws.freeze_panes = 'A2'
    d1.download_button("⬇️ Excel", data=buf.getvalue(), file_name=f"{nome_arquivo}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    d2.download_button("⬇️ CSV", data=tabela.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig'),
                       file_name=f"{nome_arquivo}.csv", mime="text/csv")


# ─── Tabelas com filtros ─────────────────────────────────────────────────────
if tipo in ("cliente", "servico", "detalhe"):
    rel = filtros(preparar_itens(df_raw))
    horas_df = load_horas(HORAS_FILE.stat().st_mtime if HORAS_FILE.exists() else None)
    tem_horas = not horas_df.empty
    corte = rel[rel['unidade'] == 'ha']
    ha_tot = corte['quantidade'].sum()
    hha_tot = horas_por_ha(rel, horas_df)
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Itens de venda", fmt_num(len(rel)))
    k2.metric("Hectares cortados", fmt_num(ha_tot, 1))
    k3.metric("Valor unit. médio do corte", fmt_brl(corte['valor_bruto'].sum() / ha_tot) if ha_tot else "—")
    k4.metric("Valor total", fmt_brl(rel['valor_bruto'].sum()))
    k5.metric("Horas p/ ha", fmt_num(hha_tot, 2) if pd.notna(hha_tot) else "aguardando planilha")

    if tipo == "cliente":
        linhas = []
        for cli, g in rel.groupby('cliente'):
            c = g[g['unidade'] == 'ha']
            ha = c['quantidade'].sum()
            linhas.append({
                'Cliente': cli,
                'Cidade': g['cidade'].mode().iloc[0] if g['cidade'].notna().any() else '',
                'Nº safras': g['safra_venda'].nunique(),
                'Hectares': ha,
                'Valor unit. corte (R$/ha)': c['valor_bruto'].sum() / ha if ha else None,
                'Valor total (R$)': g['valor_bruto'].sum(),
                'Horas p/ ha': horas_por_ha(g, horas_df),
            })
        tabela = pd.DataFrame(linhas).sort_values('Valor total (R$)', ascending=False) if linhas else pd.DataFrame()
        nota = "Valor unitário do corte considera só os itens de corte; o valor total inclui caminhões, trator e terceiros."
    elif tipo == "servico":
        tabela = (rel.groupby(['produto', 'categoria', 'unidade'], as_index=False)
                     .agg(qtd=('quantidade', 'sum'), vt=('valor_bruto', 'sum'), cli=('cliente', 'nunique')))
        tabela['vu'] = tabela['vt'] / tabela['qtd'].replace(0, np.nan)
        tabela = tabela[['produto', 'categoria', 'unidade', 'qtd', 'vu', 'vt', 'cli']].sort_values('vt', ascending=False)
        tabela.columns = ['Serviço / máquina', 'Categoria', 'Un.', 'Quantidade', 'Valor unit. médio (R$)',
                          'Valor total (R$)', 'Clientes']
        nota = "Valor unitário médio = valor total ÷ quantidade."
    else:
        tabela = rel[['data_venda', 'num_venda', 'cliente', 'cidade', 'safra_venda', 'produto',
                      'quantidade', 'unidade', 'valor_unitario', 'valor_bruto']].copy()
        if tem_horas:
            hpa = (corte.groupby(['cliente', 'safra_venda'], as_index=False)['quantidade'].sum()
                        .merge(horas_df, left_on=['cliente', 'safra_venda'], right_on=['cliente', 'safra']))
            hpa['hpa'] = hpa['horas'] / hpa['quantidade']
            tabela = tabela.merge(hpa[['cliente', 'safra_venda', 'hpa']], on=['cliente', 'safra_venda'], how='left')
            tabela.loc[tabela['unidade'] != 'ha', 'hpa'] = np.nan
        else:
            tabela['hpa'] = np.nan
        tabela = tabela.sort_values(['data_venda', 'num_venda'], ascending=False)
        tabela.columns = ['Data', 'Nº venda', 'Cliente', 'Cidade', 'Safra', 'Serviço / máquina',
                          'Qtd.', 'Un.', 'Valor unit. (R$)', 'Valor total (R$)', 'Horas p/ ha']
        nota = "A safra da venda vale para todos os itens dela (caminhões, trator e frete inclusive)."

    st.caption(nota + ("" if tem_horas else " Horas p/ ha aparece quando a planilha de horas trabalhadas for incluída."))
    st.caption("Clique no ▾ do título de uma coluna para filtrar pelos valores dela, como no Excel.")
    tabela_excel(tabela, chave=tipo, arquivo=f"relatorio_{tipo}", altura=540,
                 grupo='Nº venda' if tipo == 'detalhe' else None,
                 grupo_rotulo='Cliente' if tipo == 'detalhe' else None)

# ─── PDFs ────────────────────────────────────────────────────────────────────
elif tipo == "pdf_cliente":
    cli = st.selectbox("Cliente", sorted(df_raw[df_raw['is_silagem']]['cliente'].dropna().unique()),
                       index=None, placeholder="Selecione o cliente…")
    if cli and st.button("📥 Gerar PDF", type="primary"):
        with st.spinner("Gerando relatório…"):
            pdf = relatorio_cliente(df_raw, cli)
        st.download_button("⬇️ Baixar PDF", data=pdf, file_name=f"relatorio_cliente_{cli.replace(' ', '_')[:40]}.pdf",
                           mime="application/pdf")

elif tipo == "pdf_safra":
    safras = sorted(df_raw[df_raw['is_silagem'] & (df_raw['safra'] != 'Outros Serviços')]['safra'].dropna().unique())
    sfr = st.selectbox("Safra", safras, index=None, placeholder="Selecione a safra…")
    if sfr and st.button("📥 Gerar PDF", type="primary"):
        with st.spinner("Gerando relatório…"):
            pdf = relatorio_safra(df_raw, sfr)
        st.download_button("⬇️ Baixar PDF", data=pdf, file_name=f"relatorio_safra_{sfr.replace(' ', '_')}.pdf",
                           mime="application/pdf")

elif tipo == "pdf_ano":
    anos = sorted(df_raw['ano_agricola'].dropna().unique(), reverse=True)
    ano = st.selectbox("Ano agrícola (dezembro a novembro)", anos, index=0)
    if st.button("📥 Gerar PDF", type="primary"):
        with st.spinner("Gerando relatório…"):
            pdf = relatorio_anual(df_raw, ano)
        st.download_button("⬇️ Baixar PDF", data=pdf, file_name=f"relatorio_anual_{ano.replace('/', '-')}.pdf",
                           mime="application/pdf")

# ─── Resumo executivo ────────────────────────────────────────────────────────
elif tipo == "resumo":
    df = filtros(preparar_itens(df_raw))
    fat, liq = df['valor_bruto'].sum(), df['valor_liquido'].sum()
    ha = df['hectares'].sum()
    vendas = df.groupby('num_venda').agg(fat=('valor_bruto', 'sum'), ha=('hectares', 'sum'))
    vendas_ha = vendas[vendas['ha'] > 0]
    ticket = (vendas_ha['fat'] / vendas_ha['ha']).mean() if len(vendas_ha) else 0
    cli = (df.groupby('cliente').agg(fat=('valor_bruto', 'sum'), ha=('hectares', 'sum'),
                                     cidade=('cidade', lambda x: x.mode().iloc[0] if x.notna().any() else ''))
             .sort_values('fat', ascending=False).reset_index())
    top5 = cli.head(5)['fat'].sum() / fat * 100 if fat else 0
    top10 = cli.head(10)['fat'].sum() / fat * 100 if fat else 0

    a, b, c = st.columns(3)
    a.metric("Faturamento bruto", fmt_brl(fat))
    b.metric("Receita líquida", fmt_brl(liq), f"{(liq / fat * 100 if fat else 0):.1f}% do bruto".replace('.', ','), delta_color="off")
    c.metric("Ticket médio por hectare", fmt_brl(ticket))
    a, b, c = st.columns(3)
    a.metric("Hectares cortados", f"{fmt_num(ha, 1)} ha")
    b.metric("Clientes / vendas", f"{fmt_num(len(cli))} / {fmt_num(df['num_venda'].nunique())}")
    c.metric("Concentração top 5 / top 10", f"{top5:.1f}% / {top10:.1f}%".replace('.', ','))

    st.markdown("##### Maiores clientes")
    t = cli.head(10).rename(columns={'cliente': 'Cliente', 'cidade': 'Cidade', 'fat': 'Faturamento (R$)', 'ha': 'Hectares'})
    tabela_excel(t[['Cliente', 'Cidade', 'Faturamento (R$)', 'Hectares']], chave='resumo_top', arquivo='maiores_clientes', altura=380)

    st.markdown("##### Faturamento mensal")
    mensal = df.groupby(df['data_venda'].dt.to_period('M').astype(str))['valor_bruto'].sum().reset_index()
    mensal.columns = ['Mês', 'Faturamento']
    fig = px.bar(mensal, x='Mês', y='Faturamento', color_discrete_sequence=['#2E6B2A'])
    fig.update_layout(height=320, margin=dict(l=8, r=8, t=10, b=8), xaxis_title="", yaxis_title="R$",
                      plot_bgcolor="#FFFFFF", separators=",.")
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# ─── Exportar base ───────────────────────────────────────────────────────────
elif tipo == "exportar":
    df = filtros(preparar_itens(df_raw))
    exp = df[['num_venda', 'data_venda', 'cliente', 'cidade', 'categoria', 'produto', 'safra_venda',
              'quantidade', 'unidade', 'valor_unitario', 'valor_bruto', 'valor_liquido']].copy()
    exp.columns = ['Nº venda', 'Data', 'Cliente', 'Cidade', 'Categoria', 'Serviço / máquina', 'Safra',
                   'Qtd.', 'Un.', 'Valor unit. (R$)', 'Valor bruto (R$)', 'Valor líquido (R$)']
    st.caption(f"{fmt_num(len(exp))} itens de {fmt_num(exp['Nº venda'].nunique())} vendas com os filtros acima.")
    baixar(exp, "agrosilagem_vendas", "Vendas")
