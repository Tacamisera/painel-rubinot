# ===============================================================
# 📦 IMPORTAÇÕES E FUNÇÕES AUXILIARES
# ---------------------------------------------------------------
# Bibliotecas, timezone e funções utilitárias para:
# • Obter o intervalo do dia no fuso horário brasileiro
# • Calcular diferenças de XP, nível ou rank entre datas
# • Formatar setas visuais para variações
# ===============================================================

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time
import pytz

# ⏰ Retorna o início e o fim do dia no fuso horário informado
def get_intervalo_dia_local(agora_utc, fuso="America/Sao_Paulo"):
    brt = pytz.timezone(fuso)
    hoje_brt = agora_utc.astimezone(brt).date()
    inicio = brt.localize(datetime.combine(hoje_brt, time(0, 0)))
    fim = inicio + timedelta(hours=23, minutes=59, seconds=59)
    return inicio.astimezone(pytz.UTC), fim.astimezone(pytz.UTC)

# 🔢 Calcula a diferença entre o primeiro e o último valor de um campo dentro do período
def calcular_delta(df, nome, campo, inicio, fim):
    dados = df[df["Name"] == nome].sort_values("DataHora")
    periodo = dados[(dados["DataHora"] >= inicio) & (dados["DataHora"] <= fim)]
    if periodo.empty or len(periodo) == 1:
        return 0
    reg_inicio = periodo.iloc[0]
    reg_fim = periodo.iloc[-1]
    return int(reg_fim[campo]) - int(reg_inicio[campo])

# 🔼 Retorna HTML com cor e seta para mostrar variações no resumo individual
def seta_unicode(valor, tipo):
    if valor > 0:
        return f"<span style='color:green'>▲ {valor}</span>"
    elif valor < 0:
        return f"<span style='color:red'>▼ {abs(valor)}</span>"
    return "–"



# ===============================================================
# 📂 CARREGAR O CSV COM OS DADOS
# ---------------------------------------------------------------
# Tenta carregar o arquivo 'top100.csv' com parsing de datas.
# Interrompe o app com uma mensagem caso o arquivo falhe ou esteja vazio.
# ===============================================================

try:
    df = pd.read_csv("top100.csv", parse_dates=["DataHora"])
except Exception as e:
    st.error(f"❌ Erro ao carregar 'top100.csv': {e}")
    st.stop()

if df.empty or df["DataHora"].isna().all():
    st.warning("📭 O arquivo está vazio ou sem datas válidas.")
    st.stop()

# ===============================================================
# 🧼 LIMPEZA E PRÉ-PROCESSAMENTO DOS DADOS
# ---------------------------------------------------------------
# Trata colunas de datas e números, remove dados inválidos
# e ordena cronologicamente por personagem
# ===============================================================

# 🔁 Converte datas para datetime com UTC
df["DataHora"] = pd.to_datetime(df["DataHora"], utc=True)

# 🔢 Converte campos numéricos com tratamento de erro
df["Level"] = pd.to_numeric(df["Level"], errors="coerce")
df["Rank"] = pd.to_numeric(df["Rank"], errors="coerce")
df["Points"] = pd.to_numeric(df["Points"], errors="coerce")

# 🧽 Remove registros sem data válida
df.dropna(subset=["DataHora"], inplace=True)

# 📚 Organiza por personagem e ordem cronológica
df.sort_values(["Name", "DataHora"], inplace=True)

# Crie uma coluna auxiliar com DataHora no fuso BRT
df["DataHora_BRT"] = df["DataHora"].dt.tz_convert("America/Sao_Paulo")

# ===============================================================
# 🕓 VARIÁVEIS GLOBAIS DE TEMPO E PERÍODOS DE REFERÊNCIA
# ---------------------------------------------------------------
# Define os períodos usados nas comparações:
# • Hoje (início e fim)
# • Início do mês e do ano
# • Primeiro e último registro disponíveis no dataset
# ===============================================================

agora = df["DataHora"].max()  # 🕒 Último timestamp registrado no CSV
brt = pytz.timezone("America/Sao_Paulo")  # Fuso horário local

# 📆 Intervalo de hoje no horário de Brasília
inicio_dia, fim_dia = get_intervalo_dia_local(agora)

# 📅 Início do mês e do ano com base no menor timestamp disponível no mês/ano
agora_brt = agora.tz_convert("America/Sao_Paulo")
inicio_mes = df[df["DataHora_BRT"].dt.month == agora_brt.month]["DataHora"].min()
if pd.isna(inicio_mes):
    # fallback: início do mês no fuso BRT convertido para UTC
    inicio_mes = agora_brt.replace(day=1, hour=0, minute=0, second=0, microsecond=0).astimezone(pytz.UTC)
inicio_ano = df[df["DataHora_BRT"].dt.year == agora_brt.year]["DataHora"].min()
if pd.isna(inicio_ano):
    inicio_ano = agora_brt.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0).astimezone(pytz.UTC)

# 🔍 Primeira e última data disponíveis na base
primeiro_registro = df["DataHora"].min()
ultimo_registro = agora
# ===============================================================
# ⚙️ CONFIGURAÇÃO DO LAYOUT E TÍTULO PRINCIPAL
# ---------------------------------------------------------------
# Define a aparência da página e exibe o título com:
# • Período atual do dia (BRT)
# • Data/hora da última atualização do CSV
# ===============================================================

st.set_page_config(page_title="TOP 100 XP Elysian", layout="wide")

# 🎯 Título com período e última atualização
inicio_fmt = inicio_dia.astimezone(brt).strftime('%d/%m %H:%M')
fim_fmt = fim_dia.astimezone(brt).strftime('%d/%m %H:%M')
ultimo_fmt = ultimo_registro.astimezone(brt).strftime('%d/%m %H:%M:%S')

st.markdown(f"""
# 🏆 TOP 100 XP Elysian  
<small>
📅 <b>Período do dia:</b> {inicio_fmt} → {fim_fmt} (horário local)  
📌 <b>Última atualização:</b> <span style='color:green'>{ultimo_fmt}</span>
</small>
""", unsafe_allow_html=True)

# ===============================================================
# 🧭 SIDEBAR DE CONTEXTO E INSTRUÇÕES
# ---------------------------------------------------------------
# Mostra informações sobre a ferramenta, instruções de uso
# e informações técnicas do painel na lateral esquerda
# ===============================================================

with st.sidebar:
    
    # 📌 Formata a última atualização no horário de Brasília
    brt = pytz.timezone("America/Sao_Paulo")
    ultimo_fmt_sidebar = ultimo_registro.astimezone(brt).strftime('%d/%m/%Y %H:%M:%S')

    st.markdown(f"""
    Este painel mostra a evolução do TOP 100 do servidor **Elysian** no Rubinot.
    
    • Última atualização: **{ultimo_fmt_sidebar}**  
    • Variação de XP, Level e Rank (Dia, Semana, Mês, Ano)
    
    **Dica:** 
    use o seletor de personagem para visualizar a evolução detalhada ao longo do tempo.

    Doações são bem-vindas para manter o painel atualizado!

    👾 Desenvolvido por 👾: 
    **Paladina Revoltada**
    """)

    st.markdown("---")


# ===============================================================
# 🧾 TABELA TOP 100 — EVOLUÇÃO E RANKING INTERATIVO
# ---------------------------------------------------------------
# Cria um DataFrame com:
# • Último snapshot de cada personagem
# • Variação de XP, Level e Rank (Dia, Semana, Mês, Ano)
# • Tabela interativa com ícones e botão de download
# ===============================================================

st.markdown("## 🧾 <b>TOP 100 Elysian</b>", unsafe_allow_html=True)

# 🔼 Emojis visuais para variação
def seta_emoji(valor):
    if valor > 0:
        return f"🔼 {valor}"
    elif valor < 0:
        return f"🔽 {abs(valor)}"
    return "➖"

# 🧠 Calcula resumo para cada personagem
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
        "Δ Rank (7d)": seta_emoji(-delta_rank),  # Rank menor é melhor
        "XP Semana": calcular_delta(df, nome, "Points", agora - timedelta(days=7), agora),
        "XP Mês": calcular_delta(df, nome, "Points", inicio_mes, agora),
        "XP Ano": calcular_delta(df, nome, "Points", inicio_ano, agora),
    })

# 📊 Exibição e exportação
df_resumo = pd.DataFrame(resumo).sort_values("Rank Atual")
st.dataframe(df_resumo, use_container_width=True, hide_index=True)

st.download_button(
    "⬇️ Baixar tabela TOP 100",
    data=df_resumo.to_csv(index=False).encode("utf-8"),
    file_name="top100_elysian.csv",
    mime="text/csv"
)

# ===============================================================
# 📋 RESUMO CONSOLIDADO - PERSONAGEM + PERÍODOS
# ---------------------------------------------------------------

st.markdown("---")
st.header("📋 Evolução do Personagem por Período")

# 🎯 Seleção de personagem
personagem = st.selectbox("👤 Escolha o personagem:", df["Name"].unique())
df_p = df[df["Name"] == personagem].copy().sort_values("DataHora")

# 📅 Dias disponíveis com registros desse personagem
dias_disponiveis = df_p["DataHora_BRT"].dt.date.unique()
ultimo_dia = dias_disponiveis.max()

# 📆 Seletor de dia (default: último dia com registro)
data_dia = st.selectbox(
    "📅 Escolha o dia para análise:",
    sorted(dias_disponiveis),
    index=len(dias_disponiveis) - 1
)

# 🗓️ Construir intervalos
brt = pytz.timezone("America/Sao_Paulo")
inicio_dia = brt.localize(datetime.combine(data_dia, time(0, 0))).astimezone(pytz.UTC)
fim_dia = inicio_dia + timedelta(hours=23, minutes=59, seconds=59)

inicio_semana = brt.localize(datetime.combine(data_dia - timedelta(days=data_dia.weekday()), time(0, 0))).astimezone(pytz.UTC)
fim_semana = inicio_semana + timedelta(days=6, hours=23, minutes=59, seconds=59)

inicio_mes_local = datetime(data_dia.year, data_dia.month, 1, 0, 0)
inicio_mes = brt.localize(inicio_mes_local).astimezone(pytz.UTC)
if data_dia.month == 12:
    fim_mes_local = datetime(data_dia.year + 1, 1, 1, 0, 0) - timedelta(seconds=1)
else:
    fim_mes_local = datetime(data_dia.year, data_dia.month + 1, 1, 0, 0) - timedelta(seconds=1)
fim_mes = brt.localize(fim_mes_local).astimezone(pytz.UTC)

# 🔁 Função com triângulos brancos e fallback
def evolucao_formatada(df_p, inicio, fim):
    hist = df_p[(df_p["DataHora"] >= inicio) & (df_p["DataHora"] <= fim)].sort_values("DataHora")

    if len(hist) < 2:
        # Fallback somente para level e rank, XP continua 0
        ultimo = df_p.iloc[-1] if not df_p.empty else None
        if ultimo is not None:
            lvl_str = f"{int(ultimo['Level'])} ➖"
            rank_str = f"{int(ultimo['Rank'])} ➖"
            xp_str = "0"
            return lvl_str, rank_str, xp_str
        else:
            return "-", "-", "0"

    # ✅ Cálculo com dados suficientes
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

# ✅ Aplicação da função para períodos
lvl_dia, rank_dia, xp_dia = evolucao_formatada(df_p, inicio_dia, fim_dia)
lvl_sem, rank_sem, xp_sem = evolucao_formatada(df_p, inicio_semana, fim_semana)
lvl_mes, rank_mes, xp_mes = evolucao_formatada(df_p, inicio_mes, fim_mes)

# 📄 Montagem da tabela final
df_formatado = pd.DataFrame([
    {"Período": "Dia", "Level Inicial": lvl_dia, "Rank Inicial": rank_dia, "XP Ganha": xp_dia},
    {"Período": "Semana", "Level Inicial": lvl_sem, "Rank Inicial": rank_sem, "XP Ganha": xp_sem},
    {"Período": "Mês", "Level Inicial": lvl_mes, "Rank Inicial": rank_mes, "XP Ganha": xp_mes},
])

# 🎨 Exibição
st.markdown("### 📈 Progresso Consolidado")
st.dataframe(df_formatado, use_container_width=True, hide_index=True)

# 💾 Download
csv_export = df_formatado.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Baixar resumo consolidado",
    data=csv_export,
    file_name=f"{personagem}_resumo_periodos.csv",
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