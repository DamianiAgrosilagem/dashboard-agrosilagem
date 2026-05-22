"""
Processa o arquivo pivot6.csv do Conta Azul e gera data/vendas.csv.gz
Uso: python3 process_csv.py <caminho_do_csv>
"""
import sys
import pandas as pd
import io
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

def parse_br_number(s):
    if not s:
        return 0.0
    s = str(s).strip().replace('\n','').replace(' ','').replace('.','').replace(',','.')
    try:
        return float(s)
    except:
        return 0.0

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
        (['MILHO','2023'],'Safra Milho 2023'),(['MILHO','2024'],'Safra Milho 2024'),
        (['MILHO','2025'],'Safra Milho 2025'),(['MILHO','2026'],'Safra Milho 2026'),
    ]
    for keywords, label in mapping:
        if all(k in d for k in keywords):
            return label
    return 'Outros Serviços'

def propagate_safra_venda(df):
    """Propaga safra reconhecida para itens de silagem sem classificação na mesma venda."""
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

def process_csv(filepath):
    # Estratégia: ler como UTF-8 (Write tool salva UTF-8)
    # Se o conteúdo foi escrito com mojibake (Latin-1 chars em UTF-8),
    # aplicamos a correção encode('latin-1').decode('utf-8')
    df = None
    for enc in ('utf-8-sig', 'utf-8', 'latin-1', 'cp1252'):
        try:
            raw_text = Path(filepath).read_text(encoding=enc)
            # Detecta se tem mojibake (padrão Ã seguido de char Latin-1)
            if 'Ã' in raw_text and ('Ã£' in raw_text or 'Ãº' in raw_text or 'Ã§' in raw_text):
                try:
                    raw_text = raw_text.encode('latin-1').decode('utf-8')
                    print(f"[OK] Encoding mojibake corrigido (latin-1→utf-8)")
                except Exception:
                    pass
            # Remove BOM se presente
            raw_text = raw_text.lstrip('﻿')
            df = pd.read_csv(io.StringIO(raw_text), sep=',', dtype=str, on_bad_lines='skip')
            print(f"[OK] Lido com encoding={enc}, shape={df.shape}")
            break
        except Exception as e:
            print(f"[WARN] {enc}: {e}")
            df = None

    if df is None or df.empty:
        print("ERRO: não foi possível ler o arquivo.")
        sys.exit(1)

    # Normaliza colunas
    df.columns = [str(c).strip().lower() for c in df.columns]
    print("Colunas:", list(df.columns))

    MAPS = {
        'num_venda':    ['número da venda','numero da venda','número','numero'],
        'data_venda':   ['data da venda','data'],
        'situacao':     ['situação','situacao','status'],
        'cliente':      ['cliente','nome'],
        'cidade':       ['cidade do cliente','cidade'],
        'produto':      ['nome do produto/serviço','nome do produto/servico','produto/serviço','produto'],
        'safra_raw':    ['detalhes do item','safra','observação','observacao'],
        'quantidade':   ['quantidade de itens','quantidade','qtd'],
        'valor_bruto':  ['valor bruto','v. bruto'],
        'valor_liquido':['valor líquido','valor liquido','valor lÃ­quido'],
    }

    col_map = {}
    for target, candidates in MAPS.items():
        for cand in candidates:
            if cand in df.columns:
                col_map[target] = cand
                break

    print("Mapeamento:", col_map)

    out = pd.DataFrame()
    for target, src in col_map.items():
        out[target] = df[src]

    if 'produto'       not in out.columns: out['produto']       = 'Serviço'
    if 'safra_raw'     not in out.columns: out['safra_raw']     = out.get('produto', 'Serviço')
    if 'cidade'        not in out.columns: out['cidade']        = ''
    if 'quantidade'    not in out.columns: out['quantidade']    = '1'
    if 'valor_bruto'   not in out.columns: out['valor_bruto']   = out.get('valor_liquido', '0')
    if 'valor_liquido' not in out.columns: out['valor_liquido'] = out.get('valor_bruto', '0')

    out['num_venda']    = pd.to_numeric(out['num_venda'].astype(str).str.replace(r'\D','',regex=True), errors='coerce').fillna(0).astype(int)
    out['data_venda']   = pd.to_datetime(out['data_venda'], dayfirst=True, errors='coerce')
    out['quantidade']   = out['quantidade'].apply(parse_br_number)
    out['valor_bruto']  = out['valor_bruto'].apply(parse_br_number)
    out['valor_liquido']= out['valor_liquido'].apply(parse_br_number)

    # Filtra linha de totais (sem data) e valores zero
    n_before = len(out)
    out = out[out['data_venda'].notna() & (out['valor_bruto'] > 0)].copy()
    print(f"Após filtro data/valor: {n_before} → {len(out)} linhas")

    # Filtra situações inválidas
    SITUACOES_VALIDAS = {'faturada','faturado','pago','paga','emitida','concluída','concluida',
                         'aprovada','aprovado','ativa','finalizada','liquidada',
                         'pago parcial','pago parcial em atraso','atrasada'}
    if 'situacao' in out.columns:
        sit = out['situacao'].fillna('').str.strip().str.lower()
        mask_valida = sit.apply(lambda s: any(v in s for v in SITUACOES_VALIDAS) or s == '' or s == '(em branco)')
        n_cancel = (~mask_valida).sum()
        out = out[mask_valida].copy()
        if n_cancel > 0:
            print(f"Removidas {n_cancel} linhas com situação inválida (ex: Cancelada)")

    out['cidade']    = out['cidade'].fillna('').str.title().str.strip()
    out['cliente']   = out['cliente'].fillna('').str.strip()
    out['produto']   = out['produto'].fillna('').str.strip()
    out['safra_raw'] = out['safra_raw'].fillna('').str.strip()
    out['categoria'] = out['produto'].apply(categorize_produto)
    out['safra']     = out['safra_raw'].apply(extract_safra)
    out['is_silagem']= out['produto'].str.upper().str.contains(
                           'CORTE DE SILAGEM|CLAAS|FR 500|FR BIG|KRONE', na=False)
    out['hectares']  = out.apply(lambda r: r['quantidade'] if r['is_silagem'] else 0.0, axis=1)
    out = propagate_safra_venda(out)
    out['ano_mes']   = out['data_venda'].dt.to_period('M').astype(str)
    out['ano']       = out['data_venda'].dt.year
    out['mes']       = out['data_venda'].dt.month

    vl = out.groupby('num_venda')['valor_liquido'].sum().reset_index()
    vl.columns = ['num_venda','valor_liquido_total_venda']
    out = out.merge(vl, on='num_venda', how='left')

    # Salva
    out_path = DATA_DIR / 'vendas.csv.gz'
    out.to_csv(out_path, index=False, compression='gzip')
    print(f"\nSalvo: {out_path}")
    print(f"Total linhas: {len(out):,}")
    print(f"Vendas únicas: {out['num_venda'].nunique():,}")
    print(f"Faturamento bruto: R$ {out['valor_bruto'].sum():,.2f}")
    print(f"Receita líquida:   R$ {out['valor_liquido'].sum():,.2f}")
    print(f"Período: {out['data_venda'].min().date()} → {out['data_venda'].max().date()}")
    return out

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python3 process_csv.py <caminho_do_csv>")
        sys.exit(1)
    process_csv(sys.argv[1])
