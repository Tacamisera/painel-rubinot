# ===============================================================
# 📦 IMPORTAÇÕES E FUNÇÕES AUXILIARES
# ===============================================================

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time, date
import pytz
import os


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

# 🗓 Início da semana (segunda-feira)
def get_inicio_semana(agora_brt):
    inicio_semana_brt = datetime.combine(agora_brt.date() - timedelta(days=agora_brt.weekday()), time(0, 0))
    return pytz.timezone("America/Sao_Paulo").localize(inicio_semana_brt).astimezone(pytz.UTC)

# ===============================================================
# 📂 CARREGAMENTO E PRÉ-PROCESSAMENTO
# ===============================================================
URL_CSV = "https://raw.githubusercontent.com/Tacamisera/painel-rubinot/refs/heads/main/top100.csv"

@st.cache_data(ttl=600)
def carregar_csv():
    try:
        return pd.read_csv(URL_CSV, parse_dates=["DataHora"])
    except Exception as e:
        st.error(f"❌ Erro ao carregar CSV remoto: {e}")
        return pd.DataFrame()

if st.button("🔄 Atualizar dados"):
    st.rerun()

df = carregar_csv()

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
# ===============================================================
# 📊 CÁLCULOS E PERÍODOS

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
inicio_semana = get_inicio_semana(agora_brt)

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
        "XP Semana": calcular_delta(df, nome, "Points", inicio_semana, agora),
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
# 📅 VISUALIZAÇÃO HISTÓRICA TOP 100
# ===============================================================

st.markdown("---")
st.header("📅 TOP 100 Histórico")

datas_disponiveis = df["DataHora_BRT"].dt.date.unique()
data_selecionada = st.selectbox("📅 Escolha a data:", sorted(datas_disponiveis), index=len(datas_disponiveis) - 1)

fim_do_dia = brt.localize(datetime.combine(data_selecionada, time(23, 59, 59))).astimezone(pytz.UTC)
inicio_dia = brt.localize(datetime.combine(data_selecionada, time(0, 0))).astimezone(pytz.UTC)

# Cálculo dos inícios de período para a data selecionada
inicio_semana_sel = get_inicio_semana(fim_do_dia.astimezone(brt))
inicio_mes_sel = fim_do_dia.astimezone(brt).replace(day=1, hour=0, minute=0, second=0, microsecond=0).astimezone(pytz.UTC)

# Snapshot e cálculos para a data selecionada
df_dia = df[df["DataHora"] <= fim_do_dia].copy()
ultimo_snapshot_dia = df_dia[df_dia["DataHora"] == df_dia["DataHora"].max()]
top100_historico = []

for _, player in ultimo_snapshot_dia.sort_values("Rank").head(100).iterrows():
    xp_dia = calcular_delta(df, player["Name"], "Points", inicio_dia, fim_do_dia)
    xp_semana = calcular_delta(df, player["Name"], "Points", inicio_semana_sel, fim_do_dia)
    xp_mes = calcular_delta(df, player["Name"], "Points", inicio_mes_sel, fim_do_dia)
    delta_lvl = calcular_delta(df, player["Name"], "Level", inicio_dia, fim_do_dia)
    
    top100_historico.append({
        "Rank": int(player["Rank"]),
        "Nome": player["Name"],
        "Vocação": player["Vocation"],
        "Level": f"{int(player['Level'])} ({seta_emoji(delta_lvl)})",
        "XP Dia": f"{xp_dia:,}".replace(",", "."),
        "XP Semana": f"{xp_semana:,}".replace(",", "."),
        "XP Mês": f"{xp_mes:,}".replace(",", ".")
    })

st.markdown(f"### 📊 TOP 100 em {data_selecionada.strftime('%d/%m/%Y')}")
st.dataframe(pd.DataFrame(top100_historico), use_container_width=True, hide_index=True)

# ===============================================================
# 🏆 TOP 10 RANKINGS (DIA/SEMANA)
# ===============================================================

st.markdown("---")
st.header("🏆 TOP 10 Rankings")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📈 Top 10 XP do Dia")
    top10_dia = []
    # Calcula XP do dia para todos os players
    xp_players_dia = []
    for _, player in ultimo_snapshot.iterrows():
        xp_dia = calcular_delta(df, player["Name"], "Points", inicio_dia, fim_dia)
        if xp_dia > 0:  # Só inclui players que ganharam XP
            xp_players_dia.append((xp_dia, player))
    
    # Ordena por XP ganho e pega top 10
    for xp_dia, player in sorted(xp_players_dia, key=lambda x: x[0], reverse=True)[:10]:
        delta_lvl = calcular_delta(df, player["Name"], "Level", inicio_dia, fim_dia)
        delta_rank = calcular_delta(df, player["Name"], "Rank", inicio_dia, fim_dia)
        
        top10_dia.append({
            "Nome": player["Name"],
            "Level": f"{int(player['Level'])} ({seta_emoji(delta_lvl)})",
            "XP Ganho": f"{xp_dia:,}".replace(",", "."),
            "Rank": f"{int(player['Rank'])} ({seta_emoji(-delta_rank)})"
        })
    
    st.table(pd.DataFrame(top10_dia))

with col2:
    st.markdown("### 📈 Top 10 XP da Semana")
    top10_semana = []
    # Calcula XP da semana para todos os players
    xp_players_semana = []
    for _, player in ultimo_snapshot.iterrows():
        xp_semana = calcular_delta(df, player["Name"], "Points", inicio_semana, agora)
        if xp_semana > 0:  # Só inclui players que ganharam XP
            xp_players_semana.append((xp_semana, player))
    
    # Ordena por XP ganho e pega top 10
    for xp_semana, player in sorted(xp_players_semana, key=lambda x: x[0], reverse=True)[:10]:
        delta_lvl = calcular_delta(df, player["Name"], "Level", inicio_semana, agora)
        delta_rank = calcular_delta(df, player["Name"], "Rank", inicio_semana, agora)
        
        top10_semana.append({
            "Nome": player["Name"],
            "Level": f"{int(player['Level'])} ({seta_emoji(delta_lvl)})",
            "XP Ganho": f"{xp_semana:,}".replace(",", "."),
            "Rank": f"{int(player['Rank'])} ({seta_emoji(-delta_rank)})"
        })
    
    st.table(pd.DataFrame(top10_semana))
