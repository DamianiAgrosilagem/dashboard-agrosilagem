"""
CRM — Cadastro e Gestão de Clientes
Damiani Agrosilagem
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta, timezone
from database import (
    listar_clientes, buscar_cliente, criar_cliente, atualizar_cliente,
    listar_interacoes, criar_interacao,
    listar_tarefas, criar_tarefa, concluir_tarefa, cancelar_tarefa,
    importar_clientes_csv, clientes_sem_contato, tarefas_vencidas,
    CIDADES_COORDS,
)

st.set_page_config(
    page_title="Clientes — Damiani Agrosilagem",
    page_icon="🗂️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS (mesma identidade visual do dashboard principal) ────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] { background-color: #1B5E20; border-right: none; }
[data-testid="stSidebar"] * { color: #FFFFFF !important; }

[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] [data-baseweb="input"] input {
    background-color: #FFFFFF !important;
    color: #1A2E1A !important;
}
[data-baseweb="tag"] {
    background-color: #2E7D32 !important;
    color: #FFFFFF !important;
}
.crm-card {
    background: #F8FFF8; border: 1px solid #C8E6C9;
    border-radius: 10px; padding: 16px 20px; margin-bottom: 12px;
}
.crm-badge-A { background:#1B5E20; color:#fff; padding:3px 10px;
    border-radius:12px; font-size:0.78rem; font-weight:700; }
.crm-badge-B { background:#1565C0; color:#fff; padding:3px 10px;
    border-radius:12px; font-size:0.78rem; font-weight:700; }
.crm-badge-C { background:#E65100; color:#fff; padding:3px 10px;
    border-radius:12px; font-size:0.78rem; font-weight:700; }
.inter-icon { font-size:1.2rem; }
.block-container { padding-top: 2rem !important; }
</style>
""", unsafe_allow_html=True)

# ─── Estado de navegação ──────────────────────────────────────────────────────
if "crm_mode" not in st.session_state:
    st.session_state.crm_mode = "list"   # list | detail | new
if "crm_cliente_id" not in st.session_state:
    st.session_state.crm_cliente_id = None
if "crm_refresh" not in st.session_state:
    st.session_state.crm_refresh = 0

TIPO_ICONE = {
    "visita": "🤝", "ligacao": "📞", "whatsapp": "💬",
    "email": "📧", "anotacao": "📝",
}
CLASSIF_CORES = {"A": "green", "B": "blue", "C": "orange"}

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

    filtro_texto = st.text_input("Buscar cliente ou cidade", placeholder="Digite...")
    filtro_class = st.selectbox("Classificação", ["Todos", "A", "B", "C"])

    st.markdown("---")
    if st.button("➕ Novo Cliente", use_container_width=True, type="primary"):
        st.session_state.crm_mode = "new"
        st.session_state.crm_cliente_id = None
        st.rerun()

    if st.session_state.crm_mode == "detail" and st.session_state.crm_cliente_id:
        if st.button("← Voltar à Lista", use_container_width=True):
            st.session_state.crm_mode = "list"
            st.session_state.crm_cliente_id = None
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
#  MODO: NOVO CLIENTE
# ═══════════════════════════════════════════════════════════════════════════════
def render_novo_cliente():
    st.title("➕ Novo Cliente")

    with st.form("form_novo_cliente", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome / Razão Social *", placeholder="Ex: João Silva Agro")
            cpf_cnpj = st.text_input("CPF / CNPJ", placeholder="000.000.000-00")
            email = st.text_input("E-mail", placeholder="joao@fazenda.com.br")
            telefone = st.text_input("Telefone", placeholder="(54) 99999-0000")
            whatsapp = st.text_input("WhatsApp", placeholder="(54) 99999-0000")
        with col2:
            cidade_opts = sorted(CIDADES_COORDS.keys())
            cidade_sel = st.selectbox("Cidade (com coordenadas)", ["— Digitar manualmente —"] + cidade_opts)
            cidade_manual = ""
            if cidade_sel == "— Digitar manualmente —":
                cidade_manual = st.text_input("Cidade", placeholder="Não-Me-Toque")
            estado = st.text_input("Estado", value="RS", max_chars=2)
            endereco = st.text_area("Endereço", placeholder="Rua, número, bairro...", height=68)
            col_class, col_seg = st.columns(2)
            classificacao = col_class.selectbox("Classificação", ["B", "A", "C"])
            segmento = col_seg.text_input("Segmento", value="Agro")
            responsavel = st.text_input("Responsável", placeholder="Nome do vendedor")
        observacoes = st.text_area("Observações", height=80)

        submitted = st.form_submit_button("💾 Salvar Cliente", type="primary", use_container_width=True)

    if submitted:
        if not nome.strip():
            st.error("O campo Nome é obrigatório.")
            return

        cidade_final = cidade_manual.strip() if cidade_sel == "— Digitar manualmente —" else cidade_sel
        coords = CIDADES_COORDS.get(cidade_final, (None, None))

        payload = {
            "nome": nome.strip(),
            "cpf_cnpj": cpf_cnpj.strip() or None,
            "email": email.strip() or None,
            "telefone": telefone.strip() or None,
            "whatsapp": whatsapp.strip() or None,
            "cidade": cidade_final or None,
            "estado": estado.upper().strip() or "RS",
            "endereco": endereco.strip() or None,
            "lat": coords[0],
            "lng": coords[1],
            "classificacao": classificacao,
            "segmento": segmento.strip() or "Agro",
            "responsavel": responsavel.strip() or None,
            "observacoes": observacoes.strip() or None,
            "ativo": True,
        }
        novo = criar_cliente(payload)
        st.success(f"✅ Cliente **{nome}** cadastrado com sucesso!")
        st.session_state.crm_refresh += 1
        st.session_state.crm_mode = "detail"
        st.session_state.crm_cliente_id = novo["id"]
        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
#  MODO: DETALHE DO CLIENTE
# ═══════════════════════════════════════════════════════════════════════════════
def render_detalhe():
    c = buscar_cliente(st.session_state.crm_cliente_id)
    if not c:
        st.error("Cliente não encontrado.")
        st.session_state.crm_mode = "list"
        st.rerun()
        return

    badge_cls = f"crm-badge-{c.get('classificacao','B')}"
    st.markdown(
        f"<h2 style='margin:0 0 4px'>{c['nome']} "
        f"<span class='{badge_cls}'>{c.get('classificacao','B')}</span></h2>"
        f"<p style='color:#555;margin:0'>{c.get('cidade','')} — {c.get('estado','')}"
        f"{'  |  ' + c.get('responsavel','') if c.get('responsavel') else ''}</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    tab_dados, tab_inter, tab_tarefas = st.tabs(["📋 Dados", "📅 Interações", "✅ Tarefas"])

    # ── TAB DADOS ─────────────────────────────────────────────────────────────
    with tab_dados:
        with st.form("form_editar_cliente"):
            col1, col2 = st.columns(2)
            with col1:
                nome      = st.text_input("Nome / Razão Social", value=c.get("nome",""))
                cpf_cnpj  = st.text_input("CPF / CNPJ", value=c.get("cpf_cnpj","") or "")
                email     = st.text_input("E-mail", value=c.get("email","") or "")
                telefone  = st.text_input("Telefone", value=c.get("telefone","") or "")
                whatsapp  = st.text_input("WhatsApp", value=c.get("whatsapp","") or "")
            with col2:
                cidade    = st.text_input("Cidade", value=c.get("cidade","") or "")
                estado    = st.text_input("Estado", value=c.get("estado","RS") or "RS", max_chars=2)
                endereco  = st.text_area("Endereço", value=c.get("endereco","") or "", height=68)
                col_c, col_s = st.columns(2)
                classif   = col_c.selectbox("Classificação", ["A","B","C"],
                                index=["A","B","C"].index(c.get("classificacao","B")))
                segmento  = col_s.text_input("Segmento", value=c.get("segmento","Agro") or "Agro")
                responsavel = st.text_input("Responsável", value=c.get("responsavel","") or "")

            col_lat, col_lng = st.columns(2)
            lat = col_lat.number_input("Latitude", value=float(c.get("lat") or 0), format="%.6f")
            lng = col_lng.number_input("Longitude", value=float(c.get("lng") or 0), format="%.6f")

            # Auto-coordenadas pelo nome da cidade
            cidade_known = CIDADES_COORDS.get(cidade.strip())
            if cidade_known and (not c.get("lat") or not c.get("lng")):
                st.info(f"💡 Coordenadas disponíveis para **{cidade}**. Serão aplicadas ao salvar.")

            observacoes = st.text_area("Observações", value=c.get("observacoes","") or "", height=80)

            col_save, col_del = st.columns([3, 1])
            salvar = col_save.form_submit_button("💾 Salvar Alterações", type="primary", use_container_width=True)
            inativar = col_del.form_submit_button("🗑️ Inativar", use_container_width=True)

        if salvar:
            coords = CIDADES_COORDS.get(cidade.strip(), (lat or None, lng or None))
            atualizar_cliente(c["id"], {
                "nome": nome.strip(),
                "cpf_cnpj": cpf_cnpj.strip() or None,
                "email": email.strip() or None,
                "telefone": telefone.strip() or None,
                "whatsapp": whatsapp.strip() or None,
                "cidade": cidade.strip() or None,
                "estado": estado.upper().strip() or "RS",
                "endereco": endereco.strip() or None,
                "lat": coords[0] if coords[0] else None,
                "lng": coords[1] if coords[1] else None,
                "classificacao": classif,
                "segmento": segmento.strip() or "Agro",
                "responsavel": responsavel.strip() or None,
                "observacoes": observacoes.strip() or None,
            })
            st.success("✅ Dados atualizados!")
            st.session_state.crm_refresh += 1
            st.rerun()

        if inativar:
            atualizar_cliente(c["id"], {"ativo": False})
            st.warning("Cliente inativado.")
            st.session_state.crm_mode = "list"
            st.session_state.crm_refresh += 1
            st.rerun()

    # ── TAB INTERAÇÕES ────────────────────────────────────────────────────────
    with tab_inter:
        st.subheader("Registrar Interação")
        with st.form("form_interacao", clear_on_submit=True):
            col1, col2, col3 = st.columns([2, 2, 2])
            tipo = col1.selectbox("Tipo", ["visita", "ligacao", "whatsapp", "email", "anotacao"],
                                  format_func=lambda t: f"{TIPO_ICONE[t]} {t.capitalize()}")
            responsavel_i = col2.text_input("Responsável", placeholder="Seu nome")
            data_i = col3.date_input("Data", value=date.today())
            resultado = st.text_input("Resultado / Resumo", placeholder="Ex: Cliente interessado na safra 2025")
            obs_i = st.text_area("Observações detalhadas", height=80)
            enviar = st.form_submit_button("📌 Registrar", type="primary", use_container_width=True)

        if enviar:
            dt = datetime.combine(data_i, datetime.now().time()).replace(tzinfo=timezone.utc)
            criar_interacao(c["id"], tipo, responsavel_i, resultado, obs_i, dt)
            st.success("✅ Interação registrada!")
            st.rerun()

        st.markdown("---")
        st.subheader("Histórico")
        df_inter = listar_interacoes(c["id"])
        if df_inter.empty:
            st.info("Nenhuma interação registrada ainda.")
        else:
            for _, row in df_inter.iterrows():
                icone = TIPO_ICONE.get(row.get("tipo","anotacao"), "📝")
                dt_str = pd.to_datetime(row["data_hora"]).strftime("%d/%m/%Y %H:%M")
                st.markdown(
                    f"<div class='crm-card'>"
                    f"<b>{icone} {row.get('tipo','').capitalize()}</b> &nbsp;·&nbsp; "
                    f"{dt_str} &nbsp;·&nbsp; <i>{row.get('responsavel','')}</i><br>"
                    f"<b>{row.get('resultado','')}</b><br>"
                    f"<span style='color:#555;font-size:.88rem'>{row.get('observacoes','')}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

    # ── TAB TAREFAS ───────────────────────────────────────────────────────────
    with tab_tarefas:
        st.subheader("Nova Tarefa / Follow-up")
        with st.form("form_tarefa", clear_on_submit=True):
            col1, col2 = st.columns([3, 1])
            titulo_t = col1.text_input("Título da tarefa", placeholder="Ex: Ligar para fechar proposta")
            prazo_t = col2.date_input("Prazo", value=date.today() + timedelta(days=7))
            responsavel_t = st.text_input("Responsável", placeholder="Seu nome")
            desc_t = st.text_area("Descrição", height=68)
            criar_t = st.form_submit_button("✅ Criar Tarefa", type="primary", use_container_width=True)

        if criar_t and titulo_t.strip():
            prazo_dt = datetime.combine(prazo_t, datetime.min.time()).replace(tzinfo=timezone.utc)
            criar_tarefa(c["id"], titulo_t.strip(), desc_t, prazo_dt, responsavel_t)
            st.success("✅ Tarefa criada!")
            st.rerun()

        st.markdown("---")
        st.subheader("Tarefas Pendentes")
        df_tarefas = listar_tarefas(c["id"], status="pendente")
        if df_tarefas.empty:
            st.info("Nenhuma tarefa pendente.")
        else:
            for _, row in df_tarefas.iterrows():
                prazo_str = ""
                if row.get("prazo"):
                    p = pd.to_datetime(row["prazo"])
                    vencida = p < pd.Timestamp.now(tz="UTC")
                    prazo_str = f"{'🔴' if vencida else '📅'} {p.strftime('%d/%m/%Y')}"

                with st.container():
                    col_t, col_btn = st.columns([5, 1])
                    col_t.markdown(
                        f"**{row['titulo']}** &nbsp; {prazo_str}<br>"
                        f"<span style='color:#555;font-size:.85rem'>"
                        f"{row.get('descricao','') or ''}</span>",
                        unsafe_allow_html=True,
                    )
                    if col_btn.button("✅ Concluir", key=f"done_{row['id']}"):
                        concluir_tarefa(row["id"])
                        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
#  MODO: LISTA DE CLIENTES
# ═══════════════════════════════════════════════════════════════════════════════
def render_lista():
    st.title("🗂️ Clientes")

    # ── Métricas rápidas ──────────────────────────────────────────────────────
    df = listar_clientes(filtro_texto, filtro_class)
    total = len(df)
    n_a = int((df["classificacao"] == "A").sum()) if not df.empty else 0
    n_b = int((df["classificacao"] == "B").sum()) if not df.empty else 0
    n_c = int((df["classificacao"] == "C").sum()) if not df.empty else 0

    df_sem_contato = clientes_sem_contato(30)
    df_vencidas = tarefas_vencidas()

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Total de Clientes", total)
    m2.metric("Classificação A", n_a)
    m3.metric("Classificação B", n_b)
    m4.metric("Classificação C", n_c)
    m5.metric("Sem contato (30d)", len(df_sem_contato), delta=None,
              help="Clientes sem nenhuma interação nos últimos 30 dias")
    m6.metric("Tarefas vencidas", len(df_vencidas), delta=None)

    # ── Alertas ───────────────────────────────────────────────────────────────
    if len(df_vencidas) > 0:
        st.warning(f"⚠️ **{len(df_vencidas)} tarefa(s) vencida(s).** Verifique as fichas dos clientes.")
    if len(df_sem_contato) > 0:
        with st.expander(f"📋 {len(df_sem_contato)} cliente(s) sem contato há +30 dias", expanded=False):
            for _, row in df_sem_contato.iterrows():
                badge = f"crm-badge-{row.get('classificacao','B')}"
                st.markdown(
                    f"<span class='{badge}'>{row.get('classificacao','B')}</span> "
                    f"**{row['nome']}** — {row.get('cidade','')}",
                    unsafe_allow_html=True,
                )

    # ── Importar do CSV ───────────────────────────────────────────────────────
    with st.expander("⬆️ Importar clientes do CSV (Conta Azul)", expanded=False):
        st.info("Importa automaticamente todos os clientes únicos presentes no arquivo de vendas.")
        if st.button("🔄 Importar agora", type="secondary"):
            data_path = __import__("pathlib").Path(__file__).parent.parent / "data" / "vendas.csv.gz"
            if not data_path.exists():
                st.error("Arquivo vendas.csv.gz não encontrado. Faça upload primeiro.")
            else:
                df_v = __import__("pandas").read_csv(data_path, compression="gzip", parse_dates=["data_venda"])
                n = importar_clientes_csv(df_v)
                st.success(f"✅ {n} novo(s) cliente(s) importado(s)!" if n else "Nenhum cliente novo encontrado.")
                st.session_state.crm_refresh += 1
                st.rerun()

    # ── Tabela ────────────────────────────────────────────────────────────────
    st.markdown("---")
    if df.empty:
        st.info("Nenhum cliente encontrado. Use '➕ Novo Cliente' ou importe do CSV.")
        return

    # Monta tabela de exibição
    display_cols = ["nome", "cidade", "estado", "classificacao", "telefone", "responsavel"]
    existing = [c for c in display_cols if c in df.columns]
    df_show = df[existing].copy()
    df_show.columns = [c.replace("_"," ").title() for c in existing]

    # Renderiza linhas clicáveis
    for i, row in df.iterrows():
        badge = f"crm-badge-{row.get('classificacao','B')}"
        col_info, col_btn = st.columns([6, 1])
        col_info.markdown(
            f"<span class='{badge}'>{row.get('classificacao','B')}</span> "
            f"**{row['nome']}** &nbsp;·&nbsp; "
            f"<span style='color:#555'>{row.get('cidade','')}</span>"
            f"{'&nbsp;·&nbsp;<span style=\"color:#888\">'+row.get('responsavel','')+'</span>' if row.get('responsavel') else ''}",
            unsafe_allow_html=True,
        )
        if col_btn.button("Ver →", key=f"sel_{row['id']}"):
            st.session_state.crm_mode = "detail"
            st.session_state.crm_cliente_id = row["id"]
            st.rerun()


# ─── Roteador ────────────────────────────────────────────────────────────────
if st.session_state.crm_mode == "new":
    render_novo_cliente()
elif st.session_state.crm_mode == "detail":
    render_detalhe()
else:
    render_lista()
