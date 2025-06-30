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

# 🔢 Calcula a diferença entre o primeiro e o último valor de um campo
def calcular_delta(df, nome, campo, inicio, fim):
    dados = df[df["Name"] == nome].sort_values("DataHora")
    intervalo = dados[(dados["DataHora"] >= inicio) & (dados["DataHora"] <= fim)]
    if intervalo.shape[0] >= 2:
        return int(intervalo.iloc[-1][campo]) - int(intervalo.iloc[0][campo])
    return 0

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

# 📅 Início do mês e do ano com base no timestamp mais recente
inicio_mes = agora.replace(day=1)
inicio_ano = agora.replace(month=1, day=1)

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
    st.header("📘 Instruções")
    st.markdown("""
    Este painel mostra a evolução do TOP 100 do servidor **Elysian** no Rubinot.

    **🔁 Atualização automática**
    - Coleta de dados a cada 10 minutos
    - Dados processados e exibidos em tempo real

    **📊 Funcionalidades**
    - Tabela completa do TOP 100 com deltas (XP, Level, Rank)
    - Resumo individual por personagem (diário, semanal, mensal, anual)
    - Download dos dados para uso externo

    **🔍 Dica:** use o seletor de personagem para visualizar a evolução detalhada ao longo do tempo.
    """)

    st.markdown("---")
    st.caption("🔧 Desenvolvido por Iury • donates para Paladina Revoltada")


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
# 📋 RESUMO INDIVIDUAL DO PERSONAGEM
# ---------------------------------------------------------------
# Exibe evolução de XP, Level e Rank para o personagem escolhido
# com comparação em diferentes períodos (dia, semana, mês, ano)
# ===============================================================

st.markdown("---")
st.header("📋 Resumo Individual do Personagem")

# 🎯 Seleção de personagem
personagem = st.selectbox("👤 Selecione um personagem:", df["Name"].unique(), key="resumo_individual")
df_p = df[df["Name"] == personagem].sort_values("DataHora").copy()

# 📊 Compilação dos dados de progresso
resumo_ind = {
    "Período": ["Dia", "Semana", "Mês", "Ano"],
    "XP Gained": [
        calcular_delta(df, personagem, "Points", inicio_dia, fim_dia),
        calcular_delta(df, personagem, "Points", agora - timedelta(days=7), agora),
        calcular_delta(df, personagem, "Points", inicio_mes, agora),
        calcular_delta(df, personagem, "Points", inicio_ano, agora),
    ],
    "Δ Level": [
        seta_unicode(calcular_delta(df, personagem, "Level", inicio_dia, fim_dia), "level"),
        seta_unicode(calcular_delta(df, personagem, "Level", agora - timedelta(days=7), agora), "level"),
        seta_unicode(calcular_delta(df, personagem, "Level", inicio_mes, agora), "level"),
        seta_unicode(calcular_delta(df, personagem, "Level", inicio_ano, agora), "level"),
    ],
    "Δ Rank": [
        seta_unicode(-calcular_delta(df, personagem, "Rank", inicio_dia, fim_dia), "rank"),
        seta_unicode(-calcular_delta(df, personagem, "Rank", agora - timedelta(days=7), agora), "rank"),
        seta_unicode(-calcular_delta(df, personagem, "Rank", inicio_mes, agora), "rank"),
        seta_unicode(-calcular_delta(df, personagem, "Rank", inicio_ano, agora), "rank"),
    ],
}

# 🧾 Exibição dos dados formatados em HTML
df_resumo_ind = pd.DataFrame(resumo_ind)
st.markdown(df_resumo_ind.to_html(index=False, escape=False), unsafe_allow_html=True)

# 💾 Botão para baixar os dados como CSV
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