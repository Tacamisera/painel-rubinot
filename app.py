# ===============================================================
# 📦 IMPORTAÇÕES E FUNÇÕES AUXILIARES
# ===============================================================

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time, date
import pytz
import os

# Tentativa de importar autorefresh com fallback
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=600000, limit=None, key="refresh")
except ImportError:
    st.warning("🔄 Autorefresh desabilitado (streamlit-autorefresh não instalado). Para habilitar, use: pip install streamlit-autorefresh")

# ⏰ Intervalo do dia local

def get_intervalo_dia_local(agora_utc, fuso="America/Sao_Paulo"):
    brt = pytz.timezone(fuso)
    hoje_brt = agora_utc.astimezone(brt).date()
    inicio = brt.localize(datetime.combine(hoje_brt, time(0, 0)))
    fim = inicio + timedelta(hours=23, minutes=59, seconds=59)
    return inicio.astimezone(pytz.UTC), fim.astimezone(pytz.UTC)

# 🔢 Cálculo de diferenças

def calcular_delta(df, nome, campo, inicio, fim):
    dados = df[df["Name"] == nome].sort_values("DataHora")
    periodo = dados[(dados["DataHora"] >= inicio) & (dados["DataHora"] <= fim)]
    if periodo.empty or len(periodo) == 1:
        return 0
    return int(periodo.iloc[-1][campo]) - int(periodo.iloc[0][campo])

# 🔼 Setas visuais

def seta_emoji(valor):
    if valor > 0:
        return f"🔼 {valor}"
    elif valor < 0:
        return f"🔽 {abs(valor)}"
    return "➖"

# ===============================================================
# 📂 CARREGAMENTO E PRÉ-PROCESSAMENTO
# ===============================================================

try:
    df = pd.read_csv("top100.csv", parse_dates=["DataHora"])
except Exception as e:
    st.error(f"❌ Erro ao carregar 'top100.csv': {e}")
    st.stop()

caminho_csv = "top100.csv"
ultima_modif = os.path.getmtime(caminho_csv)
if "ultima_modif_salva" not in st.session_state:
    st.session_state["ultima_modif_salva"] = ultima_modif
elif st.session_state["ultima_modif_salva"] != ultima_modif:
    st.session_state["ultima_modif_salva"] = ultima_modif
    st.rerun()

if df.empty or df["DataHora"].isna().all():
    st.warning("📭 O arquivo está vazio ou sem datas válidas.")
    st.stop()

df["DataHora"] = pd.to_datetime(df["DataHora"], utc=True)
df["Level"] = pd.to_numeric(df["Level"], errors="coerce")
df["Rank"] = pd.to_numeric(df["Rank"], errors="coerce")
df["Points"] = pd.to_numeric(df["Points"], errors="coerce")
df.dropna(subset=["DataHora"], inplace=True)
df.sort_values(["Name", "DataHora"], inplace=True)
df["DataHora_BRT"] = df["DataHora"].dt.tz_convert("America/Sao_Paulo")

agora = df["DataHora"].max()
brt = pytz.timezone("America/Sao_Paulo")
inicio_dia, fim_dia = get_intervalo_dia_local(agora)
agora_brt = agora.tz_convert(brt)
inicio_mes = df[df["DataHora_BRT"].dt.month == agora_brt.month]["DataHora"].min()
if pd.isna(inicio_mes):
    inicio_mes = agora_brt.replace(day=1, hour=0, minute=0, second=0, microsecond=0).astimezone(pytz.UTC)
inicio_ano = df[df["DataHora_BRT"].dt.year == agora_brt.year]["DataHora"].min()
if pd.isna(inicio_ano):
    inicio_ano = agora_brt.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0).astimezone(pytz.UTC)

primeiro_registro = df["DataHora"].min()
ultimo_registro = agora

# ===============================================================
# 🏆 TÍTULO E CONTEXTO
# ===============================================================

st.set_page_config(page_title="TOP 100 XP Elysian", layout="wide")
inicio_fmt = inicio_dia.astimezone(brt).strftime('%d/%m %H:%M')
fim_fmt = fim_dia.astimezone(brt).strftime('%d/%m %H:%M')
ultimo_fmt = ultimo_registro.astimezone(brt).strftime('%d/%m %H:%M:%S')

st.markdown(f"""
# 🏆 TOP 100 XP Elysian
<small>
📅 <b>Período do dia:</b> {inicio_fmt} → {fim_fmt}  
📌 <b>Última atualização:</b> <span style='color:green'>{ultimo_fmt}</span>
</small>
""", unsafe_allow_html=True)

# ===============================================================
# 🧾 TABELA TOP 100
# ===============================================================

st.markdown("## 🧾 <b>TOP 100 Elysian</b>", unsafe_allow_html=True)
ultimo_snapshot = df[df["DataHora"] == df["DataHora"].max()]
nomes_top100_atuais = ultimo_snapshot.sort_values("Rank").head(100)["Name"].unique()

resumo = []
for nome in nomes_top100_atuais:
    registros = df[df["Name"] == nome].sort_values("DataHora")
    if registros.empty:
        continue
    ultimo = registros.iloc[-1]

    delta_lvl = calcular_delta(df, nome, "Level", inicio_dia, fim_dia)
    delta_rank = calcular_delta(df, nome, "Rank", agora - timedelta(days=7), agora)
    delta_xp_dia = calcular_delta(df, nome, "Points", inicio_dia, fim_dia)

    resumo.append({
        "Rank Atual": int(ultimo["Rank"]),
        "Name": nome,
        "Vocation": ultimo["Vocation"],
        "Level": int(ultimo["Level"]),
        "XP Total": int(ultimo["Points"]),
        "XP Dia": delta_xp_dia,
        "Δ Level (dia)": seta_emoji(delta_lvl),
        "Δ Rank (7d)": seta_emoji(-delta_rank),
        "XP Semana": calcular_delta(df, nome, "Points", agora - timedelta(days=7), agora),
        "XP Mês": calcular_delta(df, nome, "Points", inicio_mes, agora),
        "XP Ano": calcular_delta(df, nome, "Points", inicio_ano, agora),
    })

# 📊 Exibição e download
df_resumo = pd.DataFrame(resumo).sort_values("Rank Atual")
st.dataframe(df_resumo, use_container_width=True, hide_index=True)

st.download_button(
    "⬇️ Baixar tabela TOP 100",
    data=df_resumo.to_csv(index=False).encode("utf-8"),
    file_name="top100_elysian.csv",
    mime="text/csv"
)

# ===============================================================
# 📋 EVOLUÇÃO INDIVIDUAL POR DIA
# ===============================================================

st.markdown("---")
st.header("📋 Evolução do Personagem por Período")

personagem = st.selectbox("👤 Escolha o personagem:", df["Name"].unique())
df_p = df[df["Name"] == personagem].copy().sort_values("DataHora")
dias_disponiveis = df_p["DataHora_BRT"].dt.date.unique()
data_dia = st.selectbox("📅 Escolha o dia:", sorted(dias_disponiveis), index=len(dias_disponiveis) - 1)

fim_do_dia = brt.localize(datetime.combine(data_dia, time(23, 59, 59))).astimezone(pytz.UTC)
inicio_dia = brt.localize(datetime.combine(data_dia, time(0, 0))).astimezone(pytz.UTC)
inicio_semana = brt.localize(datetime.combine(data_dia - timedelta(days=data_dia.weekday()), time(0, 0))).astimezone(pytz.UTC)
inicio_mes = brt.localize(datetime.combine(date(data_dia.year, data_dia.month, 1), time(0, 0))).astimezone(pytz.UTC)

fim_dia = fim_semana = fim_mes = fim_do_dia

def evolucao_formatada(df_p, inicio, fim):
    hist = df_p[(df_p["DataHora"] >= inicio) & (df_p["DataHora"] <= fim)].sort_values("DataHora")
    if len(hist) < 2:
        ultimo = df_p.iloc[-1] if not df_p.empty else None
        lvl_str = f"{int(ultimo['Level'])} ➖" if ultimo is not None else "-"
        rank_str = f"{int(ultimo['Rank'])} ➖" if ultimo is not None else "-"
        xp_str = "0"
        return lvl_str, rank_str, xp_str

    lvl_ini = int(hist.iloc[0]["Level"])
    lvl_fim = int(hist.iloc[-1]["Level"])
    lvl_diff = lvl_fim - lvl_ini
    lvl_str = f"{lvl_ini} {'▲' if lvl_diff > 0 else '▼' if lvl_diff < 0 else '➖'} {abs(lvl_diff)}" if lvl_diff != 0 else f"{lvl_ini} ➖"

    rank_ini = int(hist.iloc[0]["Rank"])
    rank_fim = int(hist.iloc[-1]["Rank"])
    rank_diff = rank_ini - rank_fim
    rank_str = f"{rank_ini} {'▲' if rank_diff > 0 else '▼' if rank_diff < 0 else '➖'} {abs(rank_diff)}" if rank_diff != 0 else f"{rank_ini} ➖"

    xp_gained = int(hist.iloc[-1]["Points"]) - int(hist.iloc[0]["Points"])
    xp_str = f"{xp_gained:,.0f}".replace(",", ".")
    return lvl_str, rank_str, xp_str

lvl_dia, rank_dia, xp_dia = evolucao_formatada(df_p, inicio_dia, fim_dia)
lvl_sem, rank_sem, xp_sem = evolucao_formatada(df_p, inicio_semana, fim_semana)
lvl_mes, rank_mes, xp_mes = evolucao_formatada(df_p, inicio_mes, fim_mes)

df_formatado = pd.DataFrame([
    {"Período": "Dia", "Level": lvl_dia, "Rank": rank_dia, "XP Ganha": xp_dia},
    {"Período": "Semana (até dia)", "Level": lvl_sem, "Rank": rank_sem, "XP Ganha": xp_sem},
    {"Período": "Mês (até dia)", "Level": lvl_mes, "Rank": rank_mes, "XP Ganha": xp_mes},
])

st.markdown("### 📈 Progresso Consolidado")
st.dataframe(df_formatado, use_container_width=True, hide_index=True)

st.download_button(
    "⬇️ Baixar resumo consolidado",
    data=df_formatado.to_csv(index=False).encode("utf-8"),
    file_name=f"{personagem}_resumo_periodos.csv",
    mime="text/csv"
)

inicio_fmt = inicio_dia.astimezone(brt).strftime('%d/%m %H:%M')
fim_fmt = fim_dia.astimezone(brt).strftime('%d/%m %H:%M')
primeiro_fmt = primeiro_registro.astimezone(brt).strftime('%d/%m %H:%M')
ultimo_fmt = ultimo_registro.astimezone(brt).strftime('%d/%m %H:%M')

st.markdown("---")
st.caption("📅 <b>Períodos considerados:</b>", unsafe_allow_html=True)
st.caption(f"• <span style='color:green'>XP Dia:</span> {inicio_fmt} → {fim_fmt}", unsafe_allow_html=True)
st.caption(f"• XP Semana, Mês e Ano: {primeiro_fmt} → {ultimo_fmt}", unsafe_allow_html=True)
