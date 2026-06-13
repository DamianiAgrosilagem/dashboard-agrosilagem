"""
Módulo de acesso ao Supabase para o CRM da Damiani Agrosilagem.
"""
import streamlit as st
import pandas as pd
from supabase import create_client, Client
from typing import Optional, Dict, List
from datetime import datetime, timedelta, timezone

# Coordenadas das cidades (para geocodificação automática no import)
CIDADES_COORDS: Dict[str, tuple] = {
    "Júlio De Castilhos": (-29.2247, -53.6819),
    "Paraí": (-28.5897, -51.7803),
    "Boa Vista Do Cadeado": (-28.6186, -53.8303),
    "Condor": (-28.2264, -53.4875),
    "Rio Grande": (-32.0350, -52.0986),
    "Salto Do Jacuí": (-28.9017, -53.2133),
    "Guabiju": (-28.5428, -51.7442),
    "Ibiraiaras": (-28.3747, -51.6467),
    "São Jorge": (-28.4944, -51.2481),
    "Hulha Negra": (-31.4003, -53.8736),
    "Candiota": (-31.5578, -53.6758),
    "Cruz Alta": (-28.6389, -53.6064),
    "Santa Maria": (-29.6869, -53.8019),
    "Porto Alegre": (-30.0346, -51.2177),
    "Passo Fundo": (-28.2622, -52.4064),
    "Santiago": (-29.1897, -54.8658),
    "Ijuí": (-28.3878, -53.9147),
    "Santo Ângelo": (-28.2997, -54.2631),
    "Cachoeira Do Sul": (-30.0353, -52.8931),
    "Pelotas": (-31.7654, -52.3376),
    "Bagé": (-31.3289, -54.1056),
    "Uruguaiana": (-29.7542, -57.0883),
    "Alegrete": (-29.7833, -55.7919),
    "Santa Rosa": (-27.8711, -54.4814),
    "Erechim": (-27.6347, -52.2742),
    "Caxias Do Sul": (-29.1681, -51.1794),
    "Não-Me-Toque": (-28.4569, -52.8194),
    "Tapera": (-28.6261, -52.8697),
    "Selbach": (-28.6422, -52.9536),
    "Colorado": (-28.5494, -52.7025),
    "Victor Graeff": (-28.5072, -52.7736),
    "Quinze De Novembro": (-28.7347, -53.0972),
    "Ibirubá": (-28.6289, -53.0872),
    "Carazinho": (-28.2839, -52.7881),
    "Tupanciretã": (-29.0842, -53.8414),
    "Jóia": (-28.6539, -54.1158),
    "Palmeira Das Missões": (-27.8989, -53.3131),
    "Sarandi": (-27.9428, -52.9247),
    "Espumoso": (-28.7272, -52.8514),
    "Soledade": (-28.8272, -52.5114),
    "Fontoura Xavier": (-28.9786, -52.3431),
    "Campos Borges": (-28.8669, -53.0089),
    "Fortaleza Dos Valos": (-28.7994, -53.3008),
    "Boa Vista Do Incra": (-28.6253, -53.1047),
    "Saldanha Marinho": (-28.4364, -53.0325),
    "Panambi": (-28.3017, -53.5011),
    "Augusto Pestana": (-28.4397, -54.0036),
    "Chiapetta": (-27.9756, -53.9494),
    "Tenente Portela": (-27.3711, -53.7583),
    "Três Passos": (-27.4553, -53.9253),
    "Horizontina": (-27.6233, -54.3078),
    "Cândido Godói": (-27.9467, -54.2897),
    "Giruá": (-28.0314, -54.3536),
    "Coronel Bicaco": (-27.7208, -53.7106),
    "Lagoa Dos Três Cantos": (-28.5789, -52.7953),
}


@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── CLIENTES ────────────────────────────────────────────────────────────────

def listar_clientes(filtro: str = "", classificacao: str = "Todos") -> pd.DataFrame:
    sb = get_supabase()
    res = sb.table("clientes").select("*").eq("ativo", True).order("nome").execute()
    df = pd.DataFrame(res.data or [])
    if df.empty:
        return df
    if filtro:
        mask = (
            df["nome"].str.contains(filtro, case=False, na=False) |
            df["cidade"].str.contains(filtro, case=False, na=False)
        )
        df = df[mask]
    if classificacao != "Todos":
        df = df[df["classificacao"] == classificacao]
    return df.reset_index(drop=True)


def buscar_cliente(cliente_id: str) -> Optional[Dict]:
    sb = get_supabase()
    res = sb.table("clientes").select("*").eq("id", cliente_id).execute()
    return res.data[0] if res.data else None


def criar_cliente(dados: Dict) -> Dict:
    sb = get_supabase()
    res = sb.table("clientes").insert(dados).execute()
    return res.data[0] if res.data else {}


def atualizar_cliente(cliente_id: str, dados: Dict) -> Dict:
    sb = get_supabase()
    res = sb.table("clientes").update(dados).eq("id", cliente_id).execute()
    return res.data[0] if res.data else {}


def importar_clientes_csv(df_vendas: pd.DataFrame) -> int:
    """Importa clientes únicos do CSV de vendas (ignora duplicados pelo nome)."""
    sb = get_supabase()
    existentes = sb.table("clientes").select("nome").execute()
    nomes_existentes = {r["nome"].strip().upper() for r in (existentes.data or [])}

    clientes_df = (
        df_vendas[["cliente", "cidade"]]
        .drop_duplicates("cliente")
        .dropna(subset=["cliente"])
        .copy()
    )
    clientes_df["cliente"] = clientes_df["cliente"].str.strip()
    clientes_df["cidade"] = clientes_df["cidade"].fillna("").str.strip()

    novos = []
    for _, row in clientes_df.iterrows():
        nome = row["cliente"]
        cidade = row["cidade"]
        if not nome or nome.upper() in nomes_existentes:
            continue
        coords = CIDADES_COORDS.get(cidade, (None, None))
        novos.append({
            "nome": nome,
            "cidade": cidade,
            "estado": "RS",
            "lat": coords[0],
            "lng": coords[1],
            "classificacao": "B",
            "segmento": "Agro",
            "ativo": True,
        })

    if novos:
        # Insere em lotes de 100
        for i in range(0, len(novos), 100):
            sb.table("clientes").insert(novos[i:i+100]).execute()

    return len(novos)


def clientes_com_coords() -> pd.DataFrame:
    sb = get_supabase()
    res = sb.table("clientes").select("*").eq("ativo", True).not_.is_("lat", "null").execute()
    return pd.DataFrame(res.data or [])


# ─── INTERAÇÕES ──────────────────────────────────────────────────────────────

def listar_interacoes(cliente_id: str) -> pd.DataFrame:
    sb = get_supabase()
    res = (
        sb.table("interacoes")
        .select("*")
        .eq("cliente_id", cliente_id)
        .order("data_hora", desc=True)
        .execute()
    )
    return pd.DataFrame(res.data or [])


def criar_interacao(cliente_id: str, tipo: str, responsavel: str,
                    resultado: str, observacoes: str,
                    data_hora: Optional[datetime] = None) -> Dict:
    sb = get_supabase()
    dt = (data_hora or datetime.now(timezone.utc)).isoformat()
    res = sb.table("interacoes").insert({
        "cliente_id": cliente_id,
        "tipo": tipo,
        "responsavel": responsavel,
        "resultado": resultado,
        "observacoes": observacoes,
        "data_hora": dt,
    }).execute()
    return res.data[0] if res.data else {}


def ultima_interacao(cliente_id: str) -> Optional[str]:
    sb = get_supabase()
    res = (
        sb.table("interacoes")
        .select("data_hora")
        .eq("cliente_id", cliente_id)
        .order("data_hora", desc=True)
        .limit(1)
        .execute()
    )
    if res.data:
        return res.data[0]["data_hora"]
    return None


# ─── TAREFAS / FOLLOW-UPS ────────────────────────────────────────────────────

def listar_tarefas(cliente_id: Optional[str] = None, status: str = "pendente") -> pd.DataFrame:
    sb = get_supabase()
    q = sb.table("tarefas").select("*, clientes(nome)").eq("status", status)
    if cliente_id:
        q = q.eq("cliente_id", cliente_id)
    res = q.order("prazo").execute()
    rows = res.data or []
    for r in rows:
        if "clientes" in r and r["clientes"]:
            r["nome_cliente"] = r["clientes"]["nome"]
        r.pop("clientes", None)
    return pd.DataFrame(rows)


def criar_tarefa(cliente_id: str, titulo: str, descricao: str,
                 prazo: Optional[datetime], responsavel: str) -> Dict:
    sb = get_supabase()
    payload = {
        "cliente_id": cliente_id,
        "titulo": titulo,
        "descricao": descricao,
        "responsavel": responsavel,
        "status": "pendente",
    }
    if prazo:
        payload["prazo"] = prazo.isoformat()
    res = sb.table("tarefas").insert(payload).execute()
    return res.data[0] if res.data else {}


def concluir_tarefa(tarefa_id: str) -> None:
    sb = get_supabase()
    sb.table("tarefas").update({"status": "concluida"}).eq("id", tarefa_id).execute()


def cancelar_tarefa(tarefa_id: str) -> None:
    sb = get_supabase()
    sb.table("tarefas").update({"status": "cancelada"}).eq("id", tarefa_id).execute()


# ─── ANALYTICS CRM ───────────────────────────────────────────────────────────

def clientes_sem_contato(dias: int = 30) -> pd.DataFrame:
    """Retorna clientes que não tiveram interação nos últimos X dias."""
    sb = get_supabase()
    corte = (datetime.now(timezone.utc) - timedelta(days=dias)).isoformat()

    todos = sb.table("clientes").select("id, nome, cidade, classificacao").eq("ativo", True).execute()
    df_todos = pd.DataFrame(todos.data or [])
    if df_todos.empty:
        return df_todos

    recentes = (
        sb.table("interacoes")
        .select("cliente_id")
        .gte("data_hora", corte)
        .execute()
    )
    ids_recentes = {r["cliente_id"] for r in (recentes.data or [])}

    sem_contato = df_todos[~df_todos["id"].isin(ids_recentes)].copy()
    return sem_contato.sort_values("nome").reset_index(drop=True)


def tarefas_vencidas() -> pd.DataFrame:
    sb = get_supabase()
    agora = datetime.now(timezone.utc).isoformat()
    res = (
        sb.table("tarefas")
        .select("*, clientes(nome)")
        .eq("status", "pendente")
        .lt("prazo", agora)
        .execute()
    )
    rows = res.data or []
    for r in rows:
        if "clientes" in r and r["clientes"]:
            r["nome_cliente"] = r["clientes"]["nome"]
        r.pop("clientes", None)
    return pd.DataFrame(rows)
