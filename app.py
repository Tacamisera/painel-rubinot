# Importações e funções auxiliares
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time
import pytz

def get_intervalo_dia_local(agora_utc, fuso="America/Sao_Paulo"):
    brt = pytz.timezone(fuso)
    hoje_brt = agora_utc.astimezone(brt).date()
    inicio = brt.localize(datetime.combine(hoje_brt, time(0, 0)))
    fim = inicio + timedelta(hours=23, minutes=59, seconds=59)
    return inicio.astimezone(pytz.UTC), fim.astimezone(pytz.UTC)

def calcular_delta(df, nome, campo, inicio, fim):
    dados = df[df["Name"] == nome].sort_values("DataHora")
    intervalo = dados[(dados["DataHora"] >= inicio) & (dados["DataHora"] <= fim)]
    if intervalo.shape[0] >= 2:
        return int(intervalo.iloc[-1][campo]) - int(intervalo.iloc[0][campo])
    return 0

def seta_unicode(valor, tipo):
    if valor > 0:
        return f"<span style='color:green'>▲ {valor}</span>"
    elif valor < 0:
        return f"<span style='color:red'>▼ {abs(valor)}</span>"
    return "–"

# ⚙️ Configuração do layout
st.set_page_config(page_title="TOP 100 XP Elysian", layout="wide")
st.title("🏆 TOP 100 XP Elysian")

# 📂 Carregar o CSV
try:
    df = pd.read_csv("top100.csv", parse_dates=["DataHora"])
except Exception as e:
    st.error(f"Erro ao carregar 'top100.csv': {e}")
    st.stop()

if df.empty or df["DataHora"].isna().all():
    st.warning("📭 O arquivo está vazio ou sem datas válidas.")
    st.stop()

# 🧼 Limpeza dos dados
df["DataHora"] = pd.to_datetime(df["DataHora"], utc=True)
df["Level"] = pd.to_numeric(df["Level"], errors="coerce")
df["Rank"] = pd.to_numeric(df["Rank"], errors="coerce")
df["Points"] = pd.to_numeric(df["Points"], errors="coerce")
df.dropna(subset=["DataHora"], inplace=True)
df.sort_values(["Name", "DataHora"], inplace=True)

# 🕓 Variáveis globais
agora = df["DataHora"].max()
brt = pytz.timezone("America/Sao_Paulo")
inicio_dia, fim_dia = get_intervalo_dia_local(agora)
inicio_mes = agora.replace(day=1)
inicio_ano = agora.replace(month=1, day=1)
primeiro_registro = df["DataHora"].min()
ultimo_registro = agora

# 🧾 Tabela TOP 100 com emojis 🔼/🔽/➖ e ordenação interativa
st.markdown("## 🧾 <b>TOP 100 Elysian</b>", unsafe_allow_html=True)

def seta_emoji(valor):
    if valor > 0:
        return f"🔼 {valor}"
    elif valor < 0:
        return f"🔽 {abs(valor)}"
    return "➖"

resumo = []
for nome in df["Name"].unique():
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
        "Δ Rank (7d)": seta_emoji(-delta_rank),  # Invertido: rank menor é melhor
        "XP Semana": calcular_delta(df, nome, "Points", agora - timedelta(days=7), agora),
        "XP Mês": calcular_delta(df, nome, "Points", inicio_mes, agora),
        "XP Ano": calcular_delta(df, nome, "Points", inicio_ano, agora),
    })

df_resumo = pd.DataFrame(resumo).sort_values("Rank Atual")

st.dataframe(df_resumo, use_container_width=True, hide_index=True)

st.download_button("⬇️ Baixar tabela TOP 100",
    data=df_resumo.to_csv(index=False).encode("utf-8"),
    file_name="top100_elysian.csv",
    mime="text/csv"
)
# 📋 Resumo Individual do Personagem
st.markdown("---")
st.header("📋 Resumo Individual do Personagem")

personagem = st.selectbox("👤 Selecione um personagem:", df["Name"].unique(), key="resumo_individual")
df_p = df[df["Name"] == personagem].sort_values("DataHora").copy()

resumo_ind = {
    "Período": ["Dia", "Mês", "Ano"],
    "XP Gained": [
        calcular_delta(df, personagem, "Points", inicio_dia, fim_dia),
        calcular_delta(df, personagem, "Points", inicio_mes, agora),
        calcular_delta(df, personagem, "Points", inicio_ano, agora),
    ],
    "Δ Level": [
        seta_unicode(calcular_delta(df, personagem, "Level", inicio_dia, fim_dia), "level"),
        seta_unicode(calcular_delta(df, personagem, "Level", inicio_mes, agora), "level"),
        seta_unicode(calcular_delta(df, personagem, "Level", inicio_ano, agora), "level"),
    ],
    "Δ Rank": [
        seta_unicode(-calcular_delta(df, personagem, "Rank", inicio_dia, fim_dia), "rank"),
        seta_unicode(-calcular_delta(df, personagem, "Rank", inicio_mes, agora), "rank"),
        seta_unicode(-calcular_delta(df, personagem, "Rank", inicio_ano, agora), "rank"),
    ],
}

df_resumo_ind = pd.DataFrame(resumo_ind)
st.markdown(df_resumo_ind.to_html(index=False, escape=False), unsafe_allow_html=True)

csv_ind = df_resumo_ind.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Baixar resumo individual",
    data=csv_ind,
    file_name=f"{personagem}_resumo_individual.csv",
    mime="text/csv"
)

# 📎 Rodapé com períodos considerados
inicio_fmt = inicio_dia.astimezone(brt).strftime('%d/%m %H:%M')
fim_fmt = fim_dia.astimezone(brt).strftime('%d/%m %H:%M')
primeiro_fmt = primeiro_registro.astimezone(brt).strftime('%d/%m %H:%M')
ultimo_fmt = ultimo_registro.astimezone(brt).strftime('%d/%m %H:%M')

st.markdown("---")
st.caption("📅 <b>Períodos considerados:</b>", unsafe_allow_html=True)
st.caption(f"• <span style='color:green'>XP Dia:</span> {inicio_fmt} → {fim_fmt} (horário local)", unsafe_allow_html=True)
st.caption(f"• XP Semana, Mês e Ano: {primeiro_fmt} → {ultimo_fmt}", unsafe_allow_html=True)