# -*- coding: utf-8 -*-
# ===============================================================
# 📣 DESTAQUES E RANKINGS AUTOMÁTICOS — BOT DO DISCORD
# ===============================================================

import pandas as pd
import requests
import pytz
from datetime import datetime, timedelta
import sys
import io
import json

NOFEAR_PATH = "Nofear.json"

try:
    with open(NOFEAR_PATH, "r", encoding="utf-8") as f:
        membros_nofear = json.load(f)
except Exception as e:
    print("Erro ao carregar Nofear.json:", e)
    membros_nofear = []

# Suporte a saída UTF-8 no console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ===============================================================
# 📦 CONFIGURAÇÕES INICIAIS
# ===============================================================

WEBHOOK_URL = "https://discord.com/api/webhooks/1389360028166914201/6xpSV5Rjo1SmreX4tbldKkf6DVlR4JOWKkASnXs4EO_M_NSQ4rDtXxI-qhbe8XzLa4nt"
brt = pytz.timezone("America/Sao_Paulo")

EMOJI_POR_VOCACAO = {
    "Master Sorcerer": "🧙‍♂️",
    "Elder Druid": "🧙‍♂️",
    "Royal Paladin": "🏹",
    "Elite Knight": "⚔️",
    "Exalted Monk": "💪"
}

# ===============================================================
# 🔧 FUNÇÕES AUXILIARES
# ===============================================================

def formatar_numero(numero):
    return f"{numero:,}".replace(",", ".")

def enviar_para_discord(msg):
    print("Enviando para Discord:\n", msg)
    try:
        requests.post(WEBHOOK_URL, json={"content": msg})
    except Exception as e:
        print("Erro ao enviar mensagem para o Discord:", e)

def formatar_hora_local(datahora):
    if datahora.tzinfo is None:
        datahora = datahora.tz_localize("UTC")
    return datahora.astimezone(brt).strftime("%d/%m %H:%M")

def mostrar_delta(valor):
    return f"{valor:+}" if valor != 0 else "–"

def emoji_por_vocacao(voc):
    return EMOJI_POR_VOCACAO.get(voc, "👤")

def calcular_inicio_periodo(agora, modo):
    if modo == "diario":
        return agora.replace(hour=0, minute=0, second=0, microsecond=0)
    elif modo == "semanal":
        inicio = agora - timedelta(days=agora.weekday())
        return inicio.replace(hour=0, minute=0, second=0, microsecond=0)
    elif modo == "mensal":
        return agora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif modo == "fechar_mes_anterior":
        mes_passado = agora.replace(day=1) - timedelta(days=1)
        return mes_passado.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return None

# ===============================================================
# 🌟 DETECÇÃO DE DESTAQUES + ENTRADAS/SAÍDAS
# ===============================================================

def checar_destaques(df):
    df = df.sort_values("DataHora")
    mensagens = []

    datas_unicas = df["DataHora"].drop_duplicates().sort_values()

    if len(datas_unicas) >= 2:
        ultima_data = datas_unicas.iloc[-1]
        penultima_data = datas_unicas.iloc[-2]

        df_anterior = df[df["DataHora"] == penultima_data]
        df_atual = df[df["DataHora"] == ultima_data]

        nomes_antes = set(df_anterior["Name"])
        nomes_depois = set(df_atual["Name"])

        for nome in sorted(nomes_depois - nomes_antes):
            r = df_atual[df_atual["Name"] == nome].iloc[0]
            emoji = emoji_por_vocacao(r.get("Vocation", ""))
            mensagens.append(f"📈 Entrou no Top 100!\n{emoji} {nome} | Level: {int(r.Level)} | Rank: #{int(r.Rank)}")

        for nome in sorted(nomes_antes - nomes_depois):
            r = df_anterior[df_anterior["Name"] == nome].iloc[0]
            emoji = emoji_por_vocacao(r.get("Vocation", ""))
            mensagens.append(f"📉 Saiu do Top 100...\n{emoji} {nome} | Último Level: {int(r.Level)} | Rank: #{int(r.Rank)}")

        for nome in nomes_depois:
            grupo = df[df["Name"] == nome].sort_values("DataHora")
            ultimas_entradas = grupo[grupo["DataHora"].isin([penultima_data, ultima_data])]

            if len(ultimas_entradas) == 2:
                antes, depois = ultimas_entradas.iloc[0], ultimas_entradas.iloc[1]
                lvl_ant, lvl_atu = int(antes.Level), int(depois.Level)
                xp_ant, xp_atu = int(antes.Points), int(depois.Points)
                rk_ant, rk_atu = int(antes.Rank), int(depois.Rank)
                voc = depois.get("Vocation", "")
                emoji = emoji_por_vocacao(voc)

                delta_lvl = lvl_atu - lvl_ant
                delta_rk = rk_ant - rk_atu

                flecha_lvl = "▲" if delta_lvl > 0 else "▼" if delta_lvl < 0 else "➖"
                flecha_rk = "▲" if delta_rk > 0 else "▼" if delta_rk < 0 else "➖"

                if delta_lvl > 0:
                    mensagens.append(
                        f"{emoji} {nome} | Upou para o Level: {lvl_atu} (+{delta_lvl}) {flecha_lvl} | "
                        f"Rank: #{rk_atu} ({mostrar_delta(delta_rk)}) {flecha_rk}"
                    )
                elif xp_atu < xp_ant:
                    xp_perdido = formatar_numero(xp_ant - xp_atu)
                    mensagens.append(
                        f"{emoji} {nome} |☠️ Foi de Base ☠️ e perdeu {xp_perdido} de XP | "
                        f"Level: {lvl_atu} ({mostrar_delta(delta_lvl)}) {flecha_lvl} | "
                        f"Rank: #{rk_atu} ({mostrar_delta(delta_rk)}) {flecha_rk}"
                    )

    for msg in mensagens:
        enviar_para_discord(msg)

# ===============================================================
# 🏆 GERADOR DE RANKING
# ===============================================================

def gerar_ranking_top10(df, modo="diario"):
    agora = datetime.now(brt)
    inicio = calcular_inicio_periodo(agora, modo)

    if not inicio:
        return

    df_local = df.copy()
    df_local["DataHora"] = pd.to_datetime(df_local["DataHora"], utc=True).dt.tz_convert(brt)
    df_periodo = df_local[df_local["DataHora"] >= inicio]

    if df_periodo.empty:
        return

    evolucoes = []
    for nome, grupo in df_periodo.groupby("Name"):
        grupo = grupo.sort_values("DataHora")
        if len(grupo) < 2:
            continue

        ini, fim = grupo.iloc[0], grupo.iloc[-1]
        ganho_xp = int(fim.Points) - int(ini.Points)

        if ganho_xp > 0:
            evolucoes.append({
                "nome": nome,
                "xp": ganho_xp,
                "lvl_ini": int(ini.Level),
                "lvl_fim": int(fim.Level),
                "gain_lvl": int(fim.Level) - int(ini.Level),
                "rk_ini": int(ini.Rank),
                "rk_fim": int(fim.Rank),
                "delta_rank": int(ini.Rank) - int(fim.Rank)
            })

    if not evolucoes:
        return

    df_evol = pd.DataFrame(evolucoes)
    top10 = df_evol.nlargest(10, "xp")

    titulos = {
        "diario": f"🏆 **TOP 10 XP DO DIA** — {agora.strftime('%d/%m')}",
        "semanal": f"🏆 **TOP 10 XP DA SEMANA** — até {agora.strftime('%d/%m')}",
        "mensal": f"🏆 **TOP 10 XP DO MÊS** — {agora.strftime('%m/%Y')}",
        "fechar_mes_anterior": f"🏆 **TOP 10 XP - MÊS ANTERIOR**"
    }
    linhas = [titulos.get(modo, "🏆 **TOP 10 XP**")]

    for i, p in enumerate(top10.itertuples(), 1):
        prefixo = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        flecha_lvl = "▲" if p.gain_lvl > 0 else "—"
        flecha_rank = "▲" if p.delta_rank > 0 else "▼" if p.delta_rank < 0 else "—"

        linhas.append(
            f"{prefixo} {p.nome} | Level: {p.lvl_fim} (+{p.gain_lvl}) {flecha_lvl} | "
            f"XP: +{formatar_numero(p.xp)} | Rank: #{p.rk_fim} ({p.delta_rank:+}) {flecha_rank}"
        )

    enviar_para_discord("\n".join(linhas))

# ===============================================================
# 🚀 EXECUÇÃO PRINCIPAL
# ===============================================================

if __name__ == "__main__":
    df = pd.read_csv("csv/top100.csv", parse_dates=["DataHora"])
    checar_destaques(df)

    agora = datetime.now(brt)
    if agora.hour == 23 and 50 <= agora.minute <= 59:
        gerar_ranking_top10(df, modo="diario")

        if agora.weekday() == 6:
            gerar_ranking_top10(df, modo="semanal")

        if (agora + timedelta(days=1)).month != agora.month:
            gerar_ranking_top10(df, modo="mensal")

    # Execução manual caso deseje gerar ranking do mês anterior
    # gerar_ranking_top10(df, modo="fechar_mes_anterior")
