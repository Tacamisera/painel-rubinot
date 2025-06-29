import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time
import pytz

st.set_page_config(page_title="Painel RubinOT", layout="wide")
st.title("🧙 Painel RubinOT: Evolução Consolidada do Top 100")

# 🎒 Carrega CSV
try:
    df = pd.read_csv("top100.csv", parse_dates=["DataHora"])
except Exception as e:
    st.error(f"Erro ao carregar 'top100.csv': {e}")
    st.stop()

df.sort_values(["Name", "DataHora"], inplace=True)
df["Level"] = pd.to_numeric(df["Level"], errors="coerce")
df["Rank"] = pd.to_numeric(df["Rank"], errors="coerce")
df["Points"] = pd.to_numeric(df["Points"], errors="coerce")
df.dropna(subset=["DataHora"], inplace=True)

if df.empty or df["DataHora"].isna().all():
    st.warning("📭 O arquivo está vazio ou sem datas válidas.")
    st.stop()

# Força timezone UTC
df["DataHora"] = pd.to_datetime(df["DataHora"]).dt.tz_convert("UTC")
agora = df["DataHora"].max()

# 📊 Resumo consolidado por personagem
st.header("📊 Resumo consolidado (último registro de cada personagem)")

periodos = {
    "XP Dia": agora - timedelta(days=1),
    "XP Semana": agora - timedelta(days=7),
    "XP Mês": agora - timedelta(days=30),
    "XP Ano": agora - timedelta(days=365)
}

def calcular_xp(nome, inicio):
    dados = df[df["Name"] == nome].sort_values("DataHora")
    atual = dados[dados["DataHora"] <= agora]
    anterior = dados[dados["DataHora"] <= inicio]
    if atual.empty or anterior.empty: return 0
    return max(0, atual.iloc[-1]["Points"] - anterior.iloc[-1]["Points"])

def calcular_delta_rank(nome):
    dados = df[df["Name"] == nome].sort_values("DataHora")
    atual = dados[dados["DataHora"] <= agora]
    anterior = dados[dados["DataHora"] <= agora - timedelta(days=7)]
    if atual.empty or anterior.empty: return "➖"
    delta = anterior.iloc[-1]["Rank"] - atual.iloc[-1]["Rank"]
    return "🔼" if delta > 0 else "🔽" if delta < 0 else "➖"

resumo = []
for nome in df["Name"].unique():
    registros = df[df["Name"] == nome].sort_values("DataHora")
    if registros.empty: continue
    ultimo = registros.iloc[-1]
    linha = {
        "Rank Atual": int(ultimo["Rank"]),
        "Name": nome,
        "Vocation": ultimo["Vocation"],
        "Level": int(ultimo["Level"]),
        "XP Total": int(ultimo["Points"]),
        "XP Dia": calcular_xp(nome, periodos["XP Dia"]),
        "XP Semana": calcular_xp(nome, periodos["XP Semana"]),
        "XP Mês": calcular_xp(nome, periodos["XP Mês"]),
        "XP Ano": calcular_xp(nome, periodos["XP Ano"]),
        "Δ Rank (7d)": calcular_delta_rank(nome)
    }
    resumo.append(linha)

df_resumo = pd.DataFrame(resumo)
df_resumo = df_resumo.sort_values("Rank Atual")
st.dataframe(df_resumo, use_container_width=True, hide_index=True)

csv_resumo = df_resumo.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Baixar resumo consolidado", data=csv_resumo,
                   file_name="resumo_top100.csv", mime="text/csv")

# ⏱️ Evolução diária com corte 10:00 → 09:59
st.markdown("---")
st.header("⏱️ Evolução do dia (de 10:00 até 09:59 do dia seguinte)")

utc = pytz.UTC
hoje_real = agora.astimezone(utc).date()
inicio_dia = utc.localize(datetime.combine(hoje_real, time(10, 0)))
fim_dia = inicio_dia + timedelta(days=1) - timedelta(seconds=1)

df_dia = df[(df["DataHora"] >= inicio_dia) & (df["DataHora"] <= fim_dia)].copy()
df_dia.sort_values(["Name", "DataHora"], inplace=True)

resumo_dia = []
for nome in df_dia["Name"].unique():
    dados = df_dia[df_dia["Name"] == nome]
    if len(dados) < 2: continue
    primeiro = dados.iloc[0]
    ultimo = dados.iloc[-1]
    resumo_dia.append({
        "Rank Atual": int(ultimo["Rank"]),
        "Name": nome,
        "Vocation": ultimo["Vocation"],
        "Level Inicial": int(primeiro["Level"]),
        "Level Final": int(ultimo["Level"]),
        "Δ Level": ultimo["Level"] - primeiro["Level"],
        "XP Inicial": int(primeiro["Points"]),
        "XP Final": int(ultimo["Points"]),
        "XP Gained": int(ultimo["Points"] - primeiro["Points"])
    })

df_dia_resumo = pd.DataFrame(resumo_dia)
df_dia_resumo = df_dia_resumo.sort_values("XP Gained", ascending=False)
st.dataframe(df_dia_resumo, use_container_width=True, hide_index=True)

csv_dia = df_dia_resumo.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Baixar evolução do dia", data=csv_dia,
                   file_name="evolucao_dia.csv", mime="text/csv")