"""
Tabela com filtro no título de cada coluna, como o autofiltro do Excel.
Damiani Agrosilagem

Clique no ▾ de uma coluna: lista de valores com caixas de seleção, busca,
"Selecionar tudo" e ordenação. Totais e downloads seguem o que está filtrado.
"""
import json
from typing import Optional

import pandas as pd
import streamlit.components.v1 as stc

# Formatos de exibição por coluna: brl (R$ 1.234,56), n0/n1/n2 (casas decimais), data (dd/mm/aaaa), texto
_TEMPLATE = r"""
<!doctype html><html lang="pt-BR" translate="no"><head><meta charset="utf-8">
<script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>
<style>
  :root { --verde:#1B5E20; --verde2:#2E7D32; --linha:#E3E8E0; --suave:#F4F7F2; --texto:#1F2A1C; --mudo:#5E6658; }
  * { box-sizing: border-box; }
  body { margin:0; font: 13px/1.4 "Source Sans Pro", system-ui, -apple-system, "Segoe UI", sans-serif; color: var(--texto); background: transparent; }
  .barra { display:flex; flex-wrap:wrap; gap:8px; align-items:center; margin-bottom:8px; }
  .barra .info { color: var(--mudo); margin-right:auto; }
  .barra .info b { color: var(--texto); }
  button { font: inherit; cursor: pointer; }
  .btn { border:1px solid var(--linha); background:#fff; color:var(--texto); border-radius:8px; padding:6px 12px; }
  .btn:hover { border-color: var(--verde2); }
  .btn.prim { background: var(--verde); border-color: var(--verde); color:#fff; }
  .btn.prim:hover { background: var(--verde2); }
  .btn[hidden] { display:none; }
  .tbox { overflow:auto; border:1px solid var(--linha); border-radius:10px; background:#fff; height: __ALTURA__px; }
  table { width:100%; border-collapse:collapse; font-variant-numeric: tabular-nums; }
  th { position:sticky; top:0; z-index:2; background: var(--verde); color:#fff; text-align:left; font-weight:600;
       white-space:nowrap; padding:0; }
  th .h { display:flex; align-items:center; gap:6px; padding:8px 8px 8px 10px; }
  th .h span { flex:1; }
  th.num .h span { text-align:right; }
  th .seta { border:0; background: rgba(255,255,255,.18); color:#fff; border-radius:5px; width:22px; height:22px;
             display:grid; place-items:center; font-size:11px; flex:0 0 auto; }
  th .seta:hover { background: rgba(255,255,255,.32); }
  th .seta.ativo { background:#FFD54F; color:#1F2A1C; }
  td { padding:6px 10px; border-bottom:1px solid var(--suave); white-space:nowrap; }
  td.num { text-align:right; }
  tbody tr:nth-child(even) td { background:#FAFCF9; }
  tbody tr:hover td { background: #EEF5EA; }
  tfoot td { position:sticky; bottom:0; background:#E8F0E4; font-weight:700; border-top:2px solid #C9D9C2; }
  tr.sub td { background:#EEF3EA !important; font-weight:600; border-bottom:2px solid #D5E2CF; color:#2F4A2A; }
  .vazio { text-align:center; color:var(--mudo); padding:28px; }
  /* Menu do filtro */
  .menu { position:fixed; z-index:10; width:280px; background:#fff; border:1px solid #CFD8CA; border-radius:10px;
          box-shadow:0 8px 24px rgba(0,0,0,.18); padding:10px; display:flex; flex-direction:column; gap:8px; }
  .menu[hidden] { display:none; }
  .menu .ord { display:flex; gap:6px; }
  .menu .ord button { flex:1; border:1px solid var(--linha); background:#fff; border-radius:6px; padding:5px; }
  .menu .ord button:hover { border-color: var(--verde2); }
  .menu input[type=search] { width:100%; padding:6px 8px; border:1px solid #CFD8CA; border-radius:6px; font: inherit; }
  .menu .lista { max-height: __LISTA__px; overflow:auto; border:1px solid var(--suave); border-radius:6px; padding:4px 2px; }
  .menu label { display:flex; gap:8px; align-items:center; padding:3px 6px; border-radius:4px; cursor:pointer; }
  .menu label:hover { background: var(--suave); }
  .menu label .c { margin-left:auto; color: var(--mudo); font-size:11px; }
  .menu label.todos { font-weight:600; border-bottom:1px solid var(--suave); border-radius:0; padding-bottom:6px; margin-bottom:2px; }
  .menu .acoes { display:flex; gap:6px; justify-content:flex-end; }
  input[type=checkbox] { accent-color: var(--verde); width:15px; height:15px; }
  :focus-visible { outline: 2px solid var(--verde2); outline-offset: 1px; }
</style></head><body>
<div class="barra">
  <span class="info" id="info"></span>
  <button class="btn" id="limpar" hidden>✕ Limpar filtros</button>
  <button class="btn" id="csv">⬇ CSV</button>
  <button class="btn prim" id="xlsx">⬇ Excel</button>
</div>
<div class="tbox"><table><thead><tr id="cab"></tr></thead><tbody id="corpo"></tbody><tfoot><tr id="tot"></tr></tfoot></table></div>
<div class="menu" id="menu" hidden>
  <div class="ord"><button id="asc">Ordenar A → Z</button><button id="desc">Ordenar Z → A</button></div>
  <input type="search" id="busca" placeholder="Buscar…">
  <div class="lista" id="lista"></div>
  <div class="acoes"><button class="btn" id="mLimpar">Limpar</button><button class="btn prim" id="mOk">Aplicar</button></div>
</div>
<script>
const COLS = __COLS__;
const ROWS = __ROWS__;
const ARQ = __ARQUIVO__;
const CHAVE = "tabxl_" + __CHAVE__;
const GRUPO = __GRUPO__, GRUPO_ROT = __GRUPO_ROTULO__;

const nf = (d) => new Intl.NumberFormat('pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d });
const FMT = {
  brl: (v) => 'R$ ' + nf(2).format(v), n0: (v) => nf(0).format(v), n1: (v) => nf(1).format(v),
  n2: (v) => nf(2).format(v), data: (v) => v.slice(8, 10) + '/' + v.slice(5, 7) + '/' + v.slice(0, 4),
  texto: (v) => String(v),
};
const mostra = (c, v) => (v === null || v === undefined || v === '' || (typeof v === 'number' && isNaN(v))) ? '' : FMT[c.fmt](v);
const rotulo = (c, v) => mostra(c, v) || '(vazio)';
const esc = (s) => String(s).replace(/[&<>"]/g, (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[ch]));

let filtros = {}, ordem = null;
try { const s = JSON.parse(sessionStorage.getItem(CHAVE) || '{}'); filtros = Object.fromEntries(Object.entries(s.f || {}).map(([k, v]) => [k, new Set(v)])); ordem = s.o || null; } catch (e) {}
const salvar = () => { try { sessionStorage.setItem(CHAVE, JSON.stringify({ f: Object.fromEntries(Object.entries(filtros).map(([k, v]) => [k, [...v]])), o: ordem })); } catch (e) {} };

// Linhas que passam em todos os filtros (menos o da coluna `exceto`, para montar a lista dela)
function visiveis(exceto) {
  return ROWS.filter((r) => COLS.every((c, i) => i === exceto || !filtros[i] || filtros[i].has(rotulo(c, r[i]))));
}
function ordenar(rows) {
  if (!ordem) return rows;
  const { i, dir } = ordem, c = COLS[i];
  return rows.slice().sort((a, b) => {
    const x = a[i], y = b[i];
    if (x === null || x === '') return 1; if (y === null || y === '') return -1;
    return (c.tipo === 'num' ? x - y : String(x).localeCompare(String(y), 'pt-BR')) * dir;
  });
}

function desenhar() {
  const cab = document.getElementById('cab');
  cab.innerHTML = COLS.map((c, i) => `<th class="${c.tipo === 'num' ? 'num' : ''}"><div class="h"><span>${esc(c.nome)}${ordem && ordem.i === i ? (ordem.dir > 0 ? ' ▲' : ' ▼') : ''}</span>` +
    `<button class="seta${filtros[i] ? ' ativo' : ''}" data-i="${i}" title="Filtrar ${esc(c.nome)}" aria-label="Filtrar ${esc(c.nome)}">▾</button></div></th>`).join('');
  const rows = ordenar(visiveis(-1));
  const corpo = document.getElementById('corpo');
  const linha = (r) => '<tr>' + COLS.map((c, i) => `<td class="${c.tipo === 'num' ? 'num' : ''}">${esc(mostra(c, r[i]))}</td>`).join('') + '</tr>';
  let html = '';
  if (!rows.length) html = `<tr><td class="vazio" colspan="${COLS.length}">Nenhuma linha com esses filtros.</td></tr>`;
  else if (GRUPO < 0) html = rows.map(linha).join('');
  else {
    // Agrupa mantendo a ordem atual: cada venda aparece onde está seu primeiro item
    const grupos = new Map();
    for (const r of rows) { const k = r[GRUPO]; if (!grupos.has(k)) grupos.set(k, []); grupos.get(k).push(r); }
    for (const [k, itens] of grupos) {
      html += itens.map(linha).join('');
      if (itens.length < 2) continue;  // venda de um item só: o subtotal repetiria a linha
      const rot = GRUPO_ROT >= 0 ? ' · ' + itens[0][GRUPO_ROT] : '';
      // rótulo ocupa as colunas até a primeira coluna somada (Qtd., Valor total…)
      const ini = Math.max(1, COLS.findIndex((c) => c.total === 'soma'));
      html += `<tr class="sub"><td colspan="${ini}">Subtotal da venda ${esc(k)}${esc(rot)} · ${itens.length} ${itens.length > 1 ? 'itens' : 'item'}</td>` +
        COLS.slice(ini).map((c, j) => {
          const i = ini + j;
          if (c.total !== 'soma') return '<td></td>';
          return `<td class="num">${esc(mostra(c, itens.reduce((s, r) => s + (Number(r[i]) || 0), 0)))}</td>`;
        }).join('') + '</tr>';
    }
  }
  corpo.innerHTML = html;
  document.getElementById('tot').innerHTML = COLS.map((c, i) => {
    if (i === 0) return `<td>Total (${nf(0).format(rows.length)})</td>`;
    if (c.total !== 'soma') return '<td></td>';
    return `<td class="num">${esc(mostra(c, rows.reduce((s, r) => s + (Number(r[i]) || 0), 0)))}</td>`;
  }).join('');
  const nFil = Object.keys(filtros).length;
  document.getElementById('info').innerHTML = `<b>${nf(0).format(rows.length)}</b> de ${nf(0).format(ROWS.length)} linhas` + (nFil ? ` · ${nFil} filtro${nFil > 1 ? 's' : ''} ativo${nFil > 1 ? 's' : ''}` : '');
  document.getElementById('limpar').hidden = !nFil;
  salvar();
}

// ── Menu do filtro ──
const menu = document.getElementById('menu'), lista = document.getElementById('lista'), busca = document.getElementById('busca');
let colAberta = null, marcados = null, valores = [];

function abrirMenu(i, botao) {
  colAberta = i;
  const c = COLS[i], cont = new Map();
  for (const r of visiveis(i)) { const k = rotulo(c, r[i]); cont.set(k, (cont.get(k) || 0) + 1); }
  const brutos = new Map(); for (const r of ROWS) brutos.set(rotulo(c, r[i]), r[i]);
  valores = [...cont.keys()].sort((a, b) => {
    const x = brutos.get(a), y = brutos.get(b);
    return c.tipo === 'num' ? (Number(x) || 0) - (Number(y) || 0) : String(a).localeCompare(String(b), 'pt-BR');
  }).map((k) => [k, cont.get(k)]);
  marcados = new Set(filtros[i] ? [...filtros[i]] : valores.map(([k]) => k));
  busca.value = '';
  montarLista();
  menu.hidden = false;
  const r = botao.getBoundingClientRect();
  const w = menu.offsetWidth, h = menu.offsetHeight;
  menu.style.left = Math.max(4, Math.min(window.innerWidth - w - 4, r.right - w)) + 'px';
  menu.style.top = Math.max(4, Math.min(window.innerHeight - h - 4, r.bottom + 4)) + 'px';
  busca.focus();
}
function montarLista() {
  const q = busca.value.trim().toLowerCase();
  const vis = valores.filter(([k]) => !q || k.toLowerCase().includes(q));
  const todos = vis.length && vis.every(([k]) => marcados.has(k));
  lista.innerHTML = `<label class="todos"><input type="checkbox" id="todos" ${todos ? 'checked' : ''}> (Selecionar tudo${q ? ' da busca' : ''})</label>` +
    vis.map(([k, n], j) => `<label><input type="checkbox" data-j="${j}" ${marcados.has(k) ? 'checked' : ''}> <span>${esc(k)}</span><span class="c">${nf(0).format(n)}</span></label>`).join('');
  lista.querySelector('#todos').onchange = (e) => { vis.forEach(([k]) => e.target.checked ? marcados.add(k) : marcados.delete(k)); montarLista(); };
  lista.querySelectorAll('input[data-j]').forEach((cb) => cb.onchange = () => { const k = vis[+cb.dataset.j][0]; cb.checked ? marcados.add(k) : marcados.delete(k); montarLista(); });
}
function fecharMenu() { menu.hidden = true; colAberta = null; }

document.getElementById('cab').addEventListener('click', (e) => {
  const b = e.target.closest('.seta'); if (!b) return;
  e.stopPropagation();
  const i = +b.dataset.i; if (colAberta === i) return fecharMenu();
  abrirMenu(i, b);
});
busca.addEventListener('input', montarLista);
busca.addEventListener('keydown', (e) => { if (e.key === 'Enter') document.getElementById('mOk').click(); if (e.key === 'Escape') fecharMenu(); });
document.getElementById('mOk').onclick = () => {
  const i = colAberta;
  if (marcados.size === valores.length && valores.every(([k]) => marcados.has(k))) delete filtros[i];
  else filtros[i] = new Set(marcados);
  fecharMenu(); desenhar();
};
document.getElementById('mLimpar').onclick = () => { delete filtros[colAberta]; fecharMenu(); desenhar(); };
document.getElementById('asc').onclick = () => { ordem = { i: colAberta, dir: 1 }; fecharMenu(); desenhar(); };
document.getElementById('desc').onclick = () => { ordem = { i: colAberta, dir: -1 }; fecharMenu(); desenhar(); };
document.getElementById('limpar').onclick = () => { filtros = {}; desenhar(); };
document.addEventListener('click', (e) => { if (!menu.hidden && !menu.contains(e.target)) fecharMenu(); });
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') fecharMenu(); });

// ── Downloads do que está filtrado ──
function baixarArquivo(blob, nome) {
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = nome;
  document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 3000);
}
document.getElementById('csv').onclick = () => {
  const rows = ordenar(visiveis(-1));
  const cel = (s) => /[;"\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  const linhas = [COLS.map((c) => cel(c.nome)).join(';')].concat(rows.map((r) => COLS.map((c, i) => {
    const v = r[i]; if (v === null || v === '' || v === undefined) return '';
    if (c.tipo === 'num') return String(v).replace('.', ',');
    return cel(c.fmt === 'data' ? FMT.data(v) : String(v));
  }).join(';')));
  baixarArquivo(new Blob(['﻿' + linhas.join('\r\n')], { type: 'text/csv;charset=utf-8' }), ARQ + '.csv');
};
document.getElementById('xlsx').onclick = () => {
  if (typeof XLSX === 'undefined') return document.getElementById('csv').click();
  const rows = ordenar(visiveis(-1));
  const dados = [COLS.map((c) => c.nome)].concat(rows.map((r) => COLS.map((c, i) => {
    const v = r[i]; if (v === null || v === undefined || v === '') return null;
    return c.fmt === 'data' ? new Date(v + 'T12:00:00') : v;
  })));
  const ws = XLSX.utils.aoa_to_sheet(dados, { cellDates: true, dateNF: 'dd/mm/yyyy' });
  ws['!autofilter'] = { ref: ws['!ref'] };
  ws['!cols'] = COLS.map((c) => ({ wch: Math.min(45, Math.max(10, c.nome.length + 2, c.fmt === 'texto' ? 22 : 12)) }));
  const nfmt = { brl: '"R$" #,##0.00', n0: '#,##0', n1: '#,##0.0', n2: '#,##0.00' };
  COLS.forEach((c, i) => { if (!nfmt[c.fmt]) return;
    for (let r = 1; r <= rows.length; r++) { const cell = ws[XLSX.utils.encode_cell({ r, c: i })]; if (cell && cell.t === 'n') cell.z = nfmt[c.fmt]; } });
  const wb = XLSX.utils.book_new(); XLSX.utils.book_append_sheet(wb, ws, 'Relatório');
  XLSX.writeFile(wb, ARQ + '.xlsx');
};

desenhar();
</script></body></html>
"""


def _formato(nome, serie):
    if pd.api.types.is_datetime64_any_dtype(serie):
        return 'texto', 'data'
    if pd.api.types.is_numeric_dtype(serie):
        if '(R$' in nome:
            return 'num', 'brl'
        if nome.lower().startswith(('hectares', 'horas')):
            return 'num', 'n1' if nome.lower().startswith('hectares') else 'n2'
        if nome in ('Qtd.', 'Quantidade'):
            return 'num', 'n2'
        return 'num', 'n0'
    return 'texto', 'texto'


# Colunas que fazem sentido somar na linha de total
# (Qtd./Quantidade não: misturam ha, cargas e horas)
_SOMAVEIS = ('Hectares', 'Valor total (R$)', 'Valor bruto (R$)', 'Valor líquido (R$)', 'Faturamento (R$)')


def tabela_excel(df: pd.DataFrame, chave: str, arquivo: str, altura: int = 520, formatos: Optional[dict] = None,
                 grupo: Optional[str] = None, grupo_rotulo: Optional[str] = None):
    """Mostra `df` com filtro estilo Excel em cada coluna, totais e downloads (Excel/CSV) do que está filtrado.
    `grupo`: coluna que agrupa linhas (ex.: Nº venda) — cada grupo ganha uma linha de subtotal abaixo dos itens;
    `grupo_rotulo`: coluna mostrada no texto do subtotal (ex.: Cliente)."""
    formatos = formatos or {}
    cols, dados = [], {}
    for nome in df.columns:
        s = df[nome]
        tipo, fmt = _formato(nome, s)
        if nome in formatos:
            fmt = formatos[nome]
        if fmt == 'data':
            dados[nome] = s.dt.strftime('%Y-%m-%d').where(s.notna(), None)
        elif tipo == 'num':
            dados[nome] = s.astype(float).round(4).where(s.notna(), None)
        else:
            dados[nome] = s.where(s.notna(), None).astype(object)
        cols.append({'nome': nome, 'tipo': tipo, 'fmt': fmt, 'total': 'soma' if nome in _SOMAVEIS else None})
    linhas = pd.DataFrame(dados).values.tolist()
    linhas = [[None if (isinstance(v, float) and v != v) else v for v in r] for r in linhas]
    html = (_TEMPLATE
            .replace('__ALTURA__', str(altura))
            .replace('__LISTA__', str(max(140, min(300, altura - 200))))
            .replace('__COLS__', json.dumps(cols, ensure_ascii=False))
            .replace('__ROWS__', json.dumps(linhas, ensure_ascii=False, default=str).replace('</', '<\\/'))
            .replace('__ARQUIVO__', json.dumps(arquivo))
            .replace('__CHAVE__', json.dumps(chave))
            .replace('__GRUPO__', json.dumps(list(df.columns).index(grupo) if grupo else -1))
            .replace('__GRUPO_ROTULO__', json.dumps(list(df.columns).index(grupo_rotulo) if grupo_rotulo else -1)))
    stc.html(html, height=altura + 52, scrolling=False)
