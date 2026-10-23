"""
Base de vendas compartilhada entre o dashboard (app.py) e a Central de Relatórios.
Damiani Agrosilagem
"""
import re
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

BASE_DIR    = Path(__file__).parent
DATA_DIR    = BASE_DIR / "data"
VENDAS_FILE = DATA_DIR / "vendas.csv.gz"
HORAS_FILE  = DATA_DIR / "horas_trabalhadas.csv"


def fmt_brl(v):
    return f"R$ {v:,.2f}".replace(",","X").replace(".",",").replace("X",".")

def fmt_num(v, d=0):
    return f"{v:,.{d}f}".replace(",","X").replace(".",",").replace("X",".")


def get_ano_agricola(s: pd.Series) -> pd.Series:
    """Dez de X → 'X/XX+1'; Jan-Nov de X → 'X-1/XX'. Ex: ago/2023 → '2022/23'."""
    year  = s.dt.year
    month = s.dt.month
    start = year.where(month == 12, year - 1)
    end2  = (start + 1).astype(str).str[-2:]
    return start.astype(str) + "/" + end2


def propagate_safra_venda(df):
    """Itens de silagem com safra_raw genérico (ex: nome de motorista) ficam como
    'Outros Serviços'. Se a mesma venda possui outro item de silagem com safra
    reconhecida, propaga essa safra para os itens sem classificação."""
    sil_com_safra = df[df['is_silagem'] & (df['safra'] != 'Outros Serviços')]
    if sil_com_safra.empty:
        return df
    safra_map = sil_com_safra.groupby('num_venda')['safra'].agg(
        lambda s: s.mode().iloc[0]
    ).to_dict()
    mask = df['is_silagem'] & (df['safra'] == 'Outros Serviços') & df['num_venda'].isin(safra_map)
    df = df.copy()
    df.loc[mask, 'safra'] = df.loc[mask, 'num_venda'].map(safra_map)
    return df


def versao_base():
    """Data de modificação da base: muda o cache quando o arquivo é atualizado."""
    return VENDAS_FILE.stat().st_mtime if VENDAS_FILE.exists() else None


@st.cache_data(show_spinner=False)
def carregar_vendas(versao_arquivo=None):
    """Lê data/vendas.csv.gz. Retorna None se a base não existir."""
    if not VENDAS_FILE.exists():
        return None
    df = pd.read_csv(VENDAS_FILE, compression='gzip', parse_dates=['data_venda'])
    df['is_silagem']   = df['is_silagem'].astype(bool)
    df['hectares']     = df['hectares'].fillna(0)
    df = propagate_safra_venda(df)
    df['ano_agricola'] = get_ano_agricola(df['data_venda'])
    return df


# ─── Relatórios de serviços ─────────────────────────────────────────────────
def unidade_item(produto, categoria, safra_raw, valor_unit):
    """Unidade de cobrança do item: ha (corte), h (trator/terceiros por hora), carga (caminhão/frete)."""
    p = str(produto).upper()
    if categoria == 'Corte de Silagem' or 'CORTE, TRANSPORTE' in p:
        return 'h' if re.search(r'P/ ?HR|HORA', str(safra_raw).upper()) else 'ha'
    if 'P/HORA' in p or 'P/ HORA' in p: return 'h'
    if 'P/CARGA' in p: return 'carga'
    if categoria == 'Caminhões': return 'carga' if valor_unit <= 400 else 'un'
    if categoria == 'Ajuste de Diesel': return 'L'
    return 'un'


def preparar_itens(df):
    """Acrescenta safra da venda (vale para todos os itens dela), valor unitário e unidade."""
    sf = df[df['safra'] != 'Outros Serviços'].groupby('num_venda')['safra'].agg(lambda s: s.mode().iloc[0])
    rel = df.copy()
    rel['safra_venda'] = rel['safra'].where(rel['safra'] != 'Outros Serviços',
                                            rel['num_venda'].map(sf)).fillna('Sem safra no lançamento')
    rel['valor_unitario'] = np.where(rel['quantidade'] > 0, rel['valor_bruto'] / rel['quantidade'].replace(0, 1), 0)
    rel['unidade'] = [unidade_item(p, c, s, v) for p, c, s, v in
                      zip(rel['produto'], rel['categoria'], rel['safra_raw'], rel['valor_unitario'])]
    return rel


@st.cache_data(show_spinner=False)
def load_horas(versao_arquivo=None):
    """Horas trabalhadas informadas à parte (não existem no Conta Azul): cliente;safra;horas."""
    if not HORAS_FILE.exists():
        return pd.DataFrame(columns=['cliente', 'safra', 'horas'])
    h = pd.read_csv(HORAS_FILE, sep=';', decimal=',', dtype={'cliente': str, 'safra': str})
    h['cliente'] = h['cliente'].str.strip().str.upper()
    h['safra']   = h['safra'].str.strip()
    h['horas']   = pd.to_numeric(h['horas'], errors='coerce').fillna(0)
    return h.groupby(['cliente', 'safra'], as_index=False)['horas'].sum()


def horas_por_ha(linhas, horas_df):
    """Soma das horas informadas ÷ hectares das mesmas combinações cliente + safra."""
    if horas_df.empty:
        return np.nan
    corte = linhas[linhas['unidade'] == 'ha'].groupby(['cliente', 'safra_venda'], as_index=False)['quantidade'].sum()
    m = corte.merge(horas_df, left_on=['cliente', 'safra_venda'], right_on=['cliente', 'safra'])
    return m['horas'].sum() / m['quantidade'].sum() if m['quantidade'].sum() > 0 else np.nan
