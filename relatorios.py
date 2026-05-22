"""
Geração de relatórios PDF - Dashboard Agrosilagem
Dependência: fpdf2
"""
from fpdf import FPDF
import pandas as pd
from datetime import datetime

# ── Paleta ────────────────────────────────────────────────────────────────────
_VERDE      = (27,  94,  32)
_VERDE_M    = (76, 175,  80)
_CINZA_D    = (96, 125, 139)
_CINZA_L    = (245, 248, 245)
_LINHA_ALT  = (232, 245, 233)
_BRANCO     = (255, 255, 255)
_PRETO      = (33,  33,  33)

# ── Formatação ────────────────────────────────────────────────────────────────
def _brl(v):
    try:
        s = f"{float(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")
        return f"R$ {s}"
    except Exception:
        return "-"

def _num(v, d=1):
    try:
        return f"{float(v):,.{d}f}".replace(",","X").replace(".",",").replace("X",".")
    except Exception:
        return "-"

MESES = {1:"Jan",2:"Fev",3:"Mar",4:"Abr",5:"Mai",6:"Jun",
         7:"Jul",8:"Ago",9:"Set",10:"Out",11:"Nov",12:"Dez"}

def _safe(text):
    """Remove caracteres fora do Latin-1 para compatibilidade com fontes PDF."""
    return str(text).encode("latin-1", errors="replace").decode("latin-1")

# ── Classe base ───────────────────────────────────────────────────────────────
class _Base(FPDF):
    def __init__(self, subtitulo=""):
        super().__init__()
        self._subtitulo = subtitulo
        self.set_margins(12, 24, 12)
        self.set_auto_page_break(auto=True, margin=18)
        self.add_page()

    def header(self):
        self.set_fill_color(*_VERDE)
        self.rect(0, 0, 210, 20, "F")
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*_BRANCO)
        self.set_xy(12, 3)
        self.cell(100, 8, "AGROSILAGEM", align="L")
        self.set_font("Helvetica", "", 8)
        self.set_xy(12, 3)
        self.cell(186, 8, datetime.now().strftime("%d/%m/%Y"), align="R")
        self.set_font("Helvetica", "B", 9)
        self.set_xy(12, 11)
        self.cell(186, 8, _safe(self._subtitulo), align="L")
        self.ln(10)

    def footer(self):
        self.set_y(-13)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*_CINZA_D)
        self.cell(0, 8, f"Agrosilagem 2024-2026  |  Pagina {self.page_no()}", align="C")

    def kpi_row(self, items):
        """Linha de KPIs - até 4 caixas lado a lado."""
        n  = len(items)
        w  = 186 / n
        x0 = self.get_x()
        y0 = self.get_y()
        for label, value in items:
            self.set_fill_color(*_CINZA_L)
            self.rect(x0, y0, w - 2, 17, "F")
            self.set_font("Helvetica", "", 7)
            self.set_text_color(*_CINZA_D)
            self.set_xy(x0 + 2, y0 + 2)
            self.cell(w - 4, 5, _safe(label))
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(*_VERDE)
            self.set_xy(x0 + 2, y0 + 8)
            self.cell(w - 4, 7, _safe(str(value)))
            x0 += w
        self.ln(21)

    def section(self, title):
        self.ln(3)
        self.set_fill_color(*_VERDE)
        self.set_text_color(*_BRANCO)
        self.set_font("Helvetica", "B", 9)
        self.cell(0, 7, f"  {title}", fill=True, ln=True)
        self.ln(1)

    def thead(self, cols, widths, aligns=None):
        self.set_fill_color(*_VERDE_M)
        self.set_text_color(*_BRANCO)
        self.set_font("Helvetica", "B", 8)
        for i, (c, w) in enumerate(zip(cols, widths)):
            a = aligns[i] if aligns else "C"
            self.cell(w, 6, c, fill=True, align=a)
        self.ln()

    def trow(self, vals, widths, aligns=None, alt=False):
        self.set_fill_color(*(_LINHA_ALT if alt else _BRANCO))
        self.set_text_color(*_PRETO)
        self.set_font("Helvetica", "", 8)
        for i, (v, w) in enumerate(zip(vals, widths)):
            a = aligns[i] if aligns else "L"
            self.cell(w, 5, _safe(str(v)[:50]), fill=True, align=a)
        self.ln()

    def total_row(self, vals, widths, aligns=None):
        self.set_fill_color(*_CINZA_L)
        self.set_text_color(*_VERDE)
        self.set_font("Helvetica", "B", 8)
        for i, (v, w) in enumerate(zip(vals, widths)):
            a = aligns[i] if aligns else "L"
            self.cell(w, 6, _safe(str(v)), fill=True, align=a)
        self.ln()

    def to_bytes(self):
        return bytes(self.output())


# ── Helpers de cálculo ────────────────────────────────────────────────────────
def _ha_fat_por_venda(df):
    """Retorna DataFrame com num_venda, ha (silagem), fat (total da venda)."""
    _ha  = (df[df["is_silagem"] & (df["hectares"] > 0)]
            .groupby("num_venda")
            .agg(ha=("hectares", "sum"))
            .reset_index())
    _fat = df.groupby("num_venda").agg(fat=("valor_bruto", "sum")).reset_index()
    return _ha.merge(_fat, on="num_venda", how="left")


# ═══════════════════════════════════════════════════════════════════════════════
# RELATÓRIO 1 - CLIENTE
# ═══════════════════════════════════════════════════════════════════════════════
def relatorio_cliente(df: pd.DataFrame, cliente: str) -> bytes:
    dc = df[df["cliente"] == cliente].copy()
    if dc.empty:
        return b""

    fat   = dc["valor_bruto"].sum()
    liq   = dc["valor_liquido"].sum()
    ha    = dc[dc["is_silagem"]]["hectares"].sum()
    n_v   = dc["num_venda"].nunique()
    tkt   = fat / ha if ha > 0 else 0
    cidade = dc["cidade"].mode().iloc[0] if not dc["cidade"].mode().empty else "-"
    dt_min = dc["data_venda"].min().strftime("%m/%Y")
    dt_max = dc["data_venda"].max().strftime("%m/%Y")

    pdf = _Base(f"Relatório de Cliente - {cliente}")

    pdf.kpi_row([
        ("Faturamento Bruto",  _brl(fat)),
        ("Receita Líquida",    _brl(liq)),
        ("Total de Hectares",  _num(ha, 1) + " ha"),
        ("Ticket Médio R$/ha", _brl(tkt)),
    ])
    pdf.kpi_row([
        ("Vendas Realizadas", str(n_v)),
        ("Cidade",            cidade),
        ("Primeiro Serviço",  dt_min),
        ("Último Serviço",    dt_max),
    ])

    # ── Tabela por Safra ──────────────────────────────────────────────
    _ha_v  = (dc[dc["is_silagem"] & (dc["hectares"] > 0)]
              .groupby(["num_venda", "safra"])
              .agg(ha=("hectares", "sum"))
              .reset_index())
    _fat_v = dc.groupby("num_venda").agg(fat=("valor_bruto", "sum")).reset_index()
    _v     = _ha_v.merge(_fat_v, on="num_venda", how="left")
    sfdf   = (_v.groupby("safra")
               .agg(vendas=("num_venda", "nunique"), ha=("ha", "sum"), fat=("fat", "sum"))
               .reset_index())
    sfdf["ticket"] = sfdf["fat"] / sfdf["ha"]
    sfdf = sfdf.sort_values("fat", ascending=False)

    pdf.section("Histórico por Safra")
    cols   = ["Safra", "Vendas", "Hectares", "Faturamento", "Ticket R$/ha"]
    widths = [60, 18, 28, 45, 35]
    aligns = ["L", "C", "R", "R", "R"]
    pdf.thead(cols, widths, aligns)
    for i, (_, r) in enumerate(sfdf.iterrows()):
        pdf.trow(
            [r["safra"], str(int(r["vendas"])), _num(r["ha"], 1),
             _brl(r["fat"]), _brl(r["ticket"])],
            widths, aligns, alt=(i % 2 == 1)
        )
    pdf.total_row(["TOTAL", str(n_v), _num(ha, 1), _brl(fat), _brl(tkt)],
                  widths, aligns)

    # ── Tabela de Vendas ──────────────────────────────────────────────
    pdf.section("Detalhamento de Vendas")
    vcols   = ["Nº", "Data", "Produto / Serviço", "Hectares", "Valor Bruto"]
    vwidths = [14, 22, 84, 22, 32]
    valigns = ["C", "C", "L", "R", "R"]
    pdf.thead(vcols, vwidths, valigns)
    for i, (_, r) in enumerate(dc.sort_values("data_venda").iterrows()):
        ha_r = _num(r["hectares"], 1) if r["is_silagem"] and r["hectares"] > 0 else "-"
        dt_r = r["data_venda"].strftime("%d/%m/%Y") if pd.notna(r["data_venda"]) else "-"
        pdf.trow(
            [str(r["num_venda"]), dt_r, r["produto"][:46], ha_r, _brl(r["valor_bruto"])],
            vwidths, valigns, alt=(i % 2 == 1)
        )

    return pdf.to_bytes()


# ═══════════════════════════════════════════════════════════════════════════════
# RELATÓRIO 2 - SAFRA
# ═══════════════════════════════════════════════════════════════════════════════
def relatorio_safra(df: pd.DataFrame, safra: str) -> bytes:
    _ha_v = (df[df["is_silagem"] & (df["hectares"] > 0) & (df["safra"] == safra)]
             .groupby(["num_venda", "cliente", "cidade"])
             .agg(ha=("hectares", "sum"))
             .reset_index())
    _fat_v = df.groupby("num_venda").agg(fat=("valor_bruto", "sum")).reset_index()
    _v     = _ha_v.merge(_fat_v, on="num_venda", how="left")

    if _v.empty:
        return b""

    fat   = _v["fat"].sum()
    ha    = _v["ha"].sum()
    n_cli = _v["cliente"].nunique()
    tkt   = fat / ha if ha > 0 else 0
    n_v   = _v["num_venda"].nunique()

    # datas
    datas  = df[df["safra"] == safra]["data_venda"]
    dt_min = datas.min().strftime("%m/%Y") if not datas.empty else "-"
    dt_max = datas.max().strftime("%m/%Y") if not datas.empty else "-"

    pdf = _Base(f"Relatório de Safra - {safra}")

    pdf.kpi_row([
        ("Faturamento Total",   _brl(fat)),
        ("Total de Hectares",   _num(ha, 1) + " ha"),
        ("Ticket Médio R$/ha",  _brl(tkt)),
        ("Clientes Atendidos",  str(n_cli)),
    ])
    pdf.kpi_row([
        ("Vendas Realizadas", str(n_v)),
        ("Início",            dt_min),
        ("Fim",               dt_max),
        ("",                  ""),
    ])

    # ── Equipamentos ─────────────────────────────────────────────────
    eq_df = (df[df["is_silagem"] & (df["safra"] == safra)]
             .groupby("produto")
             .agg(ha=("hectares", "sum"), fat=("valor_bruto", "sum"))
             .reset_index())
    eq_df = eq_df[eq_df["ha"] > 0].sort_values("ha", ascending=False)

    pdf.section("Equipamentos Utilizados")
    ecols   = ["Equipamento", "Hectares", "Faturamento", "% Hectares"]
    ewidths = [86, 28, 44, 28]
    ealigns = ["L", "R", "R", "R"]
    pdf.thead(ecols, ewidths, ealigns)
    for i, (_, r) in enumerate(eq_df.iterrows()):
        pct = r["ha"] / ha * 100 if ha > 0 else 0
        pdf.trow(
            [r["produto"][:48], _num(r["ha"], 1), _brl(r["fat"]), f"{pct:.1f}%"],
            ewidths, ealigns, alt=(i % 2 == 1)
        )
    pdf.total_row(["TOTAL", _num(ha, 1), _brl(fat), "100,0%"], ewidths, ealigns)

    # ── Ranking de Clientes ──────────────────────────────────────────
    cli_sf = (_v.groupby(["cliente", "cidade"])
               .agg(ha=("ha", "sum"), fat=("fat", "sum"), vendas=("num_venda", "nunique"))
               .reset_index())
    cli_sf["ticket"] = cli_sf["fat"] / cli_sf["ha"]
    cli_sf = cli_sf.sort_values("fat", ascending=False).reset_index(drop=True)

    pdf.section("Ranking de Clientes")
    ccols   = ["#", "Cliente", "Cidade", "Ha", "Faturamento", "Ticket R$/ha"]
    cwidths = [10, 60, 32, 20, 38, 26]
    caligns = ["C", "L", "L", "R", "R", "R"]
    pdf.thead(ccols, cwidths, caligns)
    for i, (_, r) in enumerate(cli_sf.iterrows()):
        pdf.trow(
            [str(i + 1), r["cliente"][:34], r["cidade"][:18],
             _num(r["ha"], 1), _brl(r["fat"]), _brl(r["ticket"])],
            cwidths, caligns, alt=(i % 2 == 1)
        )
    pdf.total_row(
        ["", "TOTAL", "", _num(ha, 1), _brl(fat), _brl(tkt)],
        cwidths, caligns
    )

    return pdf.to_bytes()


# ═══════════════════════════════════════════════════════════════════════════════
# RELATÓRIO 3 - ANUAL
# ═══════════════════════════════════════════════════════════════════════════════
def relatorio_anual(df: pd.DataFrame, ano: int) -> bytes:
    da    = df[df["ano"] == ano].copy()
    da_ant = df[df["ano"] == ano - 1].copy()

    if da.empty:
        return b""

    fat   = da["valor_bruto"].sum()
    liq   = da["valor_liquido"].sum()
    ha    = da[da["is_silagem"]]["hectares"].sum()
    n_cli = da["cliente"].nunique()
    n_v   = da["num_venda"].nunique()
    tkt   = fat / ha if ha > 0 else 0
    margem = liq / fat * 100 if fat > 0 else 0

    fat_ant = da_ant["valor_bruto"].sum()
    ha_ant  = da_ant[da_ant["is_silagem"]]["hectares"].sum()

    def _var(novo, ant):
        if ant == 0:
            return "-"
        pct = (novo - ant) / ant * 100
        return f"+{pct:.1f}%" if pct >= 0 else f"{pct:.1f}%"

    pdf = _Base(f"Relatório Anual - {ano}")

    pdf.kpi_row([
        ("Faturamento Bruto",  _brl(fat)),
        ("Receita Líquida",    _brl(liq)),
        ("Margem",             f"{margem:.1f}%"),
        ("Ticket Médio R$/ha", _brl(tkt)),
    ])
    pdf.kpi_row([
        ("Total de Hectares",     _num(ha, 1) + " ha"),
        ("Clientes Ativos",       str(n_cli)),
        ("Vendas Realizadas",     str(n_v)),
        (f"Var. Faturamento vs {ano-1}", _var(fat, fat_ant)),
    ])

    # ── Safras do Ano ─────────────────────────────────────────────────
    _ha_v  = (da[da["is_silagem"] & (da["hectares"] > 0)]
              .groupby(["num_venda", "safra"])
              .agg(ha=("hectares", "sum"))
              .reset_index())
    _fat_v = da.groupby("num_venda").agg(fat=("valor_bruto", "sum")).reset_index()
    _sv    = _ha_v.merge(_fat_v, on="num_venda", how="left")
    sfdf   = (_sv.groupby("safra")
               .agg(vendas=("num_venda", "nunique"), ha=("ha", "sum"), fat=("fat", "sum"))
               .reset_index())
    sfdf["ticket"] = sfdf["fat"] / sfdf["ha"]
    sfdf = sfdf.sort_values("fat", ascending=False)

    pdf.section("Safras do Ano")
    scols   = ["Safra", "Vendas", "Hectares", "Faturamento", "Ticket R$/ha", "% Fat."]
    swidths = [58, 18, 25, 43, 32, 20]
    saligns = ["L", "C", "R", "R", "R", "R"]
    pdf.thead(scols, swidths, saligns)
    for i, (_, r) in enumerate(sfdf.iterrows()):
        pct = r["fat"] / fat * 100 if fat > 0 else 0
        pdf.trow(
            [r["safra"], str(int(r["vendas"])), _num(r["ha"], 1),
             _brl(r["fat"]), _brl(r["ticket"]), f"{pct:.1f}%"],
            swidths, saligns, alt=(i % 2 == 1)
        )
    ha_sf = sfdf["ha"].sum()
    pdf.total_row(
        ["TOTAL", str(n_v), _num(ha_sf, 1), _brl(fat), _brl(tkt), "100,0%"],
        swidths, saligns
    )

    # ── Top 10 Clientes ──────────────────────────────────────────────
    _ha_cli = (da[da["is_silagem"] & (da["hectares"] > 0)]
               .groupby(["num_venda", "cliente", "cidade"])
               .agg(ha=("hectares", "sum"))
               .reset_index())
    _fat_cli = da.groupby("num_venda").agg(fat_v=("valor_bruto", "sum")).reset_index()
    _vc = _ha_cli.merge(_fat_cli, on="num_venda", how="left")
    cli_ha = (_vc.groupby(["cliente", "cidade"])
               .agg(ha=("ha", "sum"), fat=("fat_v", "sum"), vendas=("num_venda", "nunique"))
               .reset_index())
    cli_ha["ticket"] = cli_ha["fat"] / cli_ha["ha"]
    cli_ha = cli_ha.sort_values("fat", ascending=False).head(10).reset_index(drop=True)

    pdf.section("Top 10 Clientes")
    ccols   = ["#", "Cliente", "Cidade", "Hectares", "Faturamento", "Ticket R$/ha"]
    cwidths = [10, 60, 32, 22, 38, 30]
    caligns = ["C", "L", "L", "R", "R", "R"]
    pdf.thead(ccols, cwidths, caligns)
    for i, (_, r) in enumerate(cli_ha.iterrows()):
        pct = r["fat"] / fat * 100 if fat > 0 else 0
        pdf.trow(
            [str(i + 1), r["cliente"][:34], r["cidade"][:18],
             _num(r["ha"], 1), _brl(r["fat"]), _brl(r["ticket"])],
            cwidths, caligns, alt=(i % 2 == 1)
        )

    # ── Evolução Mensal ──────────────────────────────────────────────
    mensal = (da.groupby("mes")
               .agg(fat=("valor_bruto", "sum"), ha_=("hectares", "sum"))
               .reset_index())

    pdf.section("Faturamento Mensal")
    mcols   = ["Mês", "Faturamento", "% do Ano"]
    mwidths = [30, 55, 30]
    maligns = ["L", "R", "R"]
    pdf.thead(mcols, mwidths, maligns)
    for i, (_, r) in enumerate(mensal.sort_values("mes").iterrows()):
        pct = r["fat"] / fat * 100 if fat > 0 else 0
        pdf.trow(
            [MESES.get(int(r["mes"]), str(r["mes"])), _brl(r["fat"]), f"{pct:.1f}%"],
            mwidths, maligns, alt=(i % 2 == 1)
        )
    pdf.total_row(["TOTAL", _brl(fat), "100,0%"], mwidths, maligns)

    # ── Comparativo com ano anterior ─────────────────────────────────
    if not da_ant.empty:
        pdf.section(f"Comparativo {ano} vs {ano - 1}")
        indicadores = [
            ("Faturamento Bruto",  _brl(fat),      _brl(fat_ant),  _var(fat, fat_ant)),
            ("Total Hectares",     _num(ha, 1),     _num(ha_ant, 1), _var(ha, ha_ant)),
            ("Clientes Ativos",    str(n_cli),      str(da_ant["cliente"].nunique()), ""),
            ("Ticket R$/ha",       _brl(tkt),
             _brl(fat_ant / ha_ant if ha_ant > 0 else 0),
             _var(tkt, fat_ant / ha_ant if ha_ant > 0 else 0)),
        ]
        icols   = ["Indicador", str(ano), str(ano - 1), "Variação"]
        iwidths = [65, 45, 45, 31]
        ialigns = ["L", "R", "R", "R"]
        pdf.thead(icols, iwidths, ialigns)
        for i, row in enumerate(indicadores):
            pdf.trow(list(row), iwidths, ialigns, alt=(i % 2 == 1))

    return pdf.to_bytes()
