# ===============================================================
# 📦 IMPORTAÇÕES E FUNÇÕES AUXILIARES
# ===============================================================

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time, date
import pytz

st.set_page_config(page_title="TOP 100 XP Elysian", layout="wide")

st.markdown("""
# 🏆 TOP 100 XP Elysian

ℹ️ **Aviso**: Se o aplicativo estiver demorando para carregar, você pode baixar o arquivo CSV diretamente [neste link](https://drive.google.com/file/d/1W-ZDR_pXC0w0tQxH6wLGLzzrO0m1kYYx/view?usp=sharing) e usar a opção "Local (Arquivo)" na barra lateral.

---
""")

def get_intervalo_dia_local(agora_utc, fuso="America/Sao_Paulo"):
    brt = pytz.timezone(fuso)
    hoje_brt = agora_utc.astimezone(brt).date()
    inicio = brt.localize(datetime.combine(hoje_brt, time(0, 0)))
    fim = inicio + timedelta(hours=23, minutes=59, seconds=59)
    return inicio.astimezone(pytz.UTC), fim.astimezone(pytz.UTC)

def calcular_delta(df_filtrado, campo, inicio, fim):
    periodo = df_filtrado[(df_filtrado["DataHora"] >= inicio) & (df_filtrado["DataHora"] <= fim)]
    if periodo.empty or len(periodo) == 1:
        return 0
    return int(periodo.iloc[-1][campo]) - int(periodo.iloc[0][campo])

def seta_emoji(valor):
    if valor > 0:
        return f"🔼 {valor}"
    elif valor < 0:
        return f"🔽 {abs(valor)}"
    return "➖"

def get_inicio_semana(agora_brt):
    inicio_semana_brt = datetime.combine(agora_brt.date() - timedelta(days=agora_brt.weekday()), time(0, 0))
    return pytz.timezone("America/Sao_Paulo").localize(inicio_semana_brt).astimezone(pytz.UTC)

# ===============================================================
# 📂 CARREGAMENTO E PRÉ-PROCESSAMENTO
# ===============================================================
URL_CSV = "https://raw.githubusercontent.com/Tacamisera/painel-rubinot/refs/heads/main/top100.csv"

@st.cache_data(ttl=600, show_spinner="Carregando dados do GitHub...")
def carregar_csv_remoto():
    try:
        df_remote = pd.read_csv(URL_CSV, parse_dates=["DataHora"])
        if df_remote.empty:
            st.warning("⚠️ O arquivo remoto está vazio.")
        return df_remote
    except Exception as e:
        st.error(f"❌ Erro ao carregar CSV remoto: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=600)
def carregar_csv_local(arquivo):
    try:
        return pd.read_csv(arquivo, parse_dates=["DataHora"])
    except Exception as e:
        st.error(f"❌ Erro ao carregar arquivo local: {e}")
        return pd.DataFrame()

# Fonte de dados na sidebar (compacto)
fonte_dados = st.sidebar.selectbox(
    "📊 Fonte dos dados:",
    ["Remoto (GitHub)", "Local (Arquivo)"],
)

if fonte_dados == "Local (Arquivo)":
    arquivo_local = st.sidebar.file_uploader("📁 Escolha o arquivo CSV", type="csv")
    if arquivo_local is not None:
        df = carregar_csv_local(arquivo_local)
    else:
        st.sidebar.warning("⚠️ Por favor, selecione um arquivo CSV")
        st.stop()
else:
    df = carregar_csv_remoto()

if st.sidebar.button("🔄 Atualizar dados"):
    st.experimental_rerun()

if df.empty or df["DataHora"].isna().all():
    st.warning("📟 O arquivo está vazio ou sem datas válidas.")
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

st.markdown("## 🧾 <b>TOP 100 Elysian</b>", unsafe_allow_html=True)
ultimo_snapshot = df[df["DataHora"] == df["DataHora"].max()]
nomes_top100_atuais = ultimo_snapshot.sort_values("Rank").head(100)["Name"].unique()

grouped = df.groupby("Name")

resumo = []
for nome in nomes_top100_atuais:
    registros = grouped.get_group(nome)
    ultimo = registros.iloc[-1]

    delta_lvl = calcular_delta(registros, "Level", inicio_dia, fim_dia)
    delta_rank = calcular_delta(registros, "Rank", agora - timedelta(days=7), agora)
    delta_xp_dia = calcular_delta(registros, "Points", inicio_dia, fim_dia)

    resumo.append({
        "Rank Atual": int(ultimo["Rank"]),
        "Name": nome,
        "Vocation": ultimo["Vocation"],
        "Level": int(ultimo["Level"]),
        "XP Total": int(ultimo["Points"]),
        "XP Dia": delta_xp_dia,
        "Δ Level (dia)": seta_emoji(delta_lvl),
        "Δ Rank (7d)": seta_emoji(-delta_rank),
        "XP Semana": calcular_delta(registros, "Points", inicio_semana, agora),
        "XP Mês": calcular_delta(registros, "Points", inicio_mes, agora),
        "XP Ano": calcular_delta(registros, "Points", inicio_ano, agora),
    })

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

st.markdown("---")
st.header("📅 TOP 100 Histórico")

datas_disponiveis = df["DataHora_BRT"].dt.date.unique()
data_selecionada = st.selectbox("📅 Escolha a data:", sorted(datas_disponiveis), index=len(datas_disponiveis) - 1, key="historico_data")

fim_do_dia = brt.localize(datetime.combine(data_selecionada, time(23, 59, 59))).astimezone(pytz.UTC)
inicio_do_dia = brt.localize(datetime.combine(data_selecionada, time(0, 0))).astimezone(pytz.UTC)

inicio_semana_hist = get_inicio_semana(fim_do_dia.astimezone(brt))
inicio_mes_hist = fim_do_dia.astimezone(brt).replace(day=1, hour=0, minute=0, second=0, microsecond=0).astimezone(pytz.UTC)
inicio_ano_hist = fim_do_dia.astimezone(brt).replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0).astimezone(pytz.UTC)

df_ate_dia = df[df["DataHora"] <= fim_do_dia]

if df_ate_dia.empty:
    st.warning(f"Não há dados disponíveis até o dia {data_selecionada.strftime('%d/%m/%Y')}")
    st.stop()

ultimo_snapshot_hist = df_ate_dia.groupby("Name").last()
nomes_top100_atuais_hist = ultimo_snapshot_hist.sort_values("Rank").head(100).index.tolist()

grouped_hist = df_ate_dia.groupby("Name")

resumo_hist = []

for nome in nomes_top100_atuais_hist:
    registros = grouped_hist.get_group(nome)
    ultimo = ultimo_snapshot_hist.loc[nome]

    delta_lvl = calcular_delta(registros, "Level", inicio_do_dia, fim_do_dia)
    delta_rank = calcular_delta(registros, "Rank", fim_do_dia - timedelta(days=7), fim_do_dia)
    delta_xp_dia = calcular_delta(registros, "Points", inicio_do_dia, fim_do_dia)

    xp_semana = calcular_delta(registros, "Points", inicio_semana_hist, fim_do_dia)
    xp_mes = calcular_delta(registros, "Points", inicio_mes_hist, fim_do_dia)
    xp_ano = calcular_delta(registros, "Points", inicio_ano_hist, fim_do_dia)

    resumo_hist.append({
        "Rank Atual": int(ultimo["Rank"]),
        "Name": nome,
        "Vocation": ultimo["Vocation"],
        "Level": int(ultimo["Level"]),
        "XP Total": int(ultimo["Points"]),
        "XP Dia": delta_xp_dia,
        "Δ Level (dia)": seta_emoji(delta_lvl),
        "Δ Rank (7d)": seta_emoji(-delta_rank),
        "XP Semana": xp_semana,
        "XP Mês": xp_mes,
        "XP Ano": xp_ano,
    })

df_resumo_hist = pd.DataFrame(resumo_hist).sort_values("Rank Atual")

st.markdown(f"### 📊 TOP 100 em {data_selecionada.strftime('%d/%m/%Y')}")
st.dataframe(df_resumo_hist, use_container_width=True, hide_index=True)

# ===============================================================
# 🏆 TOP 10 RANKINGS (DIA/SEMANA)

st.markdown("---")
st.header("🏆 TOP 10 Rankings")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📈 Top 10 XP do Dia")
    top10_dia = []
    xp_players_dia = []
    for _, player in ultimo_snapshot.iterrows():
        xp_dia = calcular_delta(grouped.get_group(player["Name"]), "Points", inicio_dia, fim_dia)
        if xp_dia > 0:
            xp_players_dia.append((xp_dia, player))

    for pos, (xp_dia, player) in enumerate(sorted(xp_players_dia, key=lambda x: x[0], reverse=True)[:10], 1):
        delta_lvl = calcular_delta(grouped.get_group(player["Name"]), "Level", inicio_dia, fim_dia)
        delta_rank = calcular_delta(grouped.get_group(player["Name"]), "Rank", inicio_dia, fim_dia)

        top10_dia.append({
            "Pos": f"#{pos}",
            "Nome": player["Name"],
            "Level": f"{int(player['Level'])} ({seta_emoji(delta_lvl)})",
            "XP Ganho": f"{xp_dia:,}".replace(",", "."),
            "Rank": f"{int(player['Rank'])} ({seta_emoji(-delta_rank)})"
        })

    st.table(pd.DataFrame(top10_dia).set_index('Pos')[['Nome', 'Level', 'XP Ganho', 'Rank']])

with col2:
    st.markdown("### 📈 Top 10 XP da Semana")
    top10_semana = []
    xp_players_semana = []
    for _, player in ultimo_snapshot.iterrows():
        xp_semana = calcular_delta(grouped.get_group(player["Name"]), "Points", inicio_semana, agora)
        if xp_semana > 0:
            xp_players_semana.append((xp_semana, player))

    for pos, (xp_semana, player) in enumerate(sorted(xp_players_semana, key=lambda x: x[0], reverse=True)[:10], 1):
        delta_lvl = calcular_delta(grouped.get_group(player["Name"]), "Level", inicio_semana, agora)
        delta_rank = calcular_delta(grouped.get_group(player["Name"]), "Rank", inicio_semana, agora)

        top10_semana.append({
            "Pos": f"#{pos}",
            "Nome": player["Name"],
            "Level": f"{int(player['Level'])} ({seta_emoji(delta_lvl)})",
            "XP Ganho": f"{xp_semana:,}".replace(",", "."),
            "Rank": f"{int(player['Rank'])} ({seta_emoji(-delta_rank)})"
        })

    st.table(pd.DataFrame(top10_semana).set_index('Pos')[['Nome', 'Level', 'XP Ganho', 'Rank']])
