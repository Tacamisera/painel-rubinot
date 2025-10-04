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
WEBHOOK_NOFEAR_URL = "https://discord.com/api/webhooks/1394517269794525355/7RF7ApPBmIl_ATlM1O2ZyP_bbBsBl_VtwFpsR2oU3_Or9w-7q-igNyKlkMtUu29EBENU"  # ⬅️ SUBSTITUA POR SEU WEBHOOK NOFEAR

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
    """Envia para o webhook principal (destaques gerais)"""
    print("Enviando para Discord Principal:\n", msg)
    try:
        requests.post(WEBHOOK_URL, json={"content": msg})
    except Exception as e:
        print("Erro ao enviar mensagem para o Discord Principal:", e)

def enviar_para_nofear_discord(msg):
    """Envia para o webhook exclusivo da Nofear"""
    print("Enviando para Discord Nofear:\n", msg)
    try:
        requests.post(WEBHOOK_NOFEAR_URL, json={"content": msg})
    except Exception as e:
        print("Erro ao enviar mensagem para o Discord Nofear:", e)

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
# 🔔 MONITORAMENTO ESPECIAL NOFEAR (WEBHOOK SEPARADO)
# ===============================================================

def monitorar_membros_nofear(df):
    """Monitora alterações nos Points dos membros da Nofear - Webhook separado"""
    if not membros_nofear:
        print("Lista Nofear vazia, pulando monitoramento...")
        return
    
    df = df.sort_values("DataHora")
    datas_unicas = df["DataHora"].drop_duplicates().sort_values()
    
    if len(datas_unicas) < 2:
        return
    
    ultima_data = datas_unicas.iloc[-1]
    penultima_data = datas_unicas.iloc[-2]
    
    df_anterior = df[df["DataHora"] == penultima_data]
    df_atual = df[df["DataHora"] == ultima_data]
    
    alertas_nofear = []
    
    for nome in membros_nofear:
        registro_antes = df_anterior[df_anterior["Name"] == nome]
        registro_agora = df_atual[df_atual["Name"] == nome]
        
        if registro_agora.empty:
            # Personagem saiu do Top 100
            if not registro_antes.empty:
                registro_antes = registro_antes.iloc[0]
                alertas_nofear.append(
                    f"⚠️ **NOFEAR SAIU DO TOP 100!**\n"
                    f"👤 {nome} | Último Level: {int(registro_antes.Level)}"
                )
            continue
            
        registro_agora = registro_agora.iloc[0]
        voc = registro_agora.get("Vocation", "")
        emoji = emoji_por_vocacao(voc)
        
        if registro_antes.empty:
            # Personagem entrou no Top 100
            alertas_nofear.append(
                f"🎯 **NOFEAR ENTROU NO TOP 100!**\n"
                f"{emoji} {nome} | Level: {int(registro_agora.Level)} | "
                f"Rank: #{int(registro_agora.Rank)}"
            )
        else:
            # Comparar alterações
            registro_antes = registro_antes.iloc[0]
            points_antes = int(registro_antes.Points)
            points_agora = int(registro_agora.Points)
            level_antes = int(registro_antes.Level)
            level_agora = int(registro_agora.Level)
            rank_antes = int(registro_antes.Rank)
            rank_agora = int(registro_agora.Rank)
            
            diferenca_points = points_agora - points_antes
            diferenca_level = level_agora - level_antes
            diferenca_rank = rank_antes - rank_agora  # Positivo = subiu no ranking
            
            if diferenca_points != 0:
                if diferenca_points > 0:
                    alertas_nofear.append(
                        f"📈 **NOFEAR XP UP!**\n"
                        f"{emoji} {nome} | +{formatar_numero(diferenca_points)} XP\n"
                        f"Level: {level_agora} ({diferenca_level:+}) | "
                        f"Rank: #{rank_agora} ({diferenca_rank:+})"
                    )
                else:
                    alertas_nofear.append(
                        f"☠️ **NOFEAR MORREU!**\n"
                        f"{emoji} {nome} | -{formatar_numero(abs(diferenca_points))} XP\n"
                        f"Level: {level_agora} | Rank: #{rank_agora}"
                    )
    
    # Enviar alertas APENAS para o webhook da Nofear
    for alerta in alertas_nofear:
        enviar_para_nofear_discord(alerta)
        print(f"Alerta Nofear enviado para webhook exclusivo: {alerta}")

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
    
    # Monitorar destaques gerais (webhook principal)
    checar_destaques(df)
    
    # Monitorar membros Nofear (webhook separado)
    monitorar_membros_nofear(df)
    
    agora = datetime.now(brt)
    if agora.hour == 23 and 50 <= agora.minute <= 59:
        gerar_ranking_top10(df, modo="diario")

        if agora.weekday() == 6:
            gerar_ranking_top10(df, modo="semanal")

        if (agora + timedelta(days=1)).month != agora.month:
            gerar_ranking_top10(df, modo="mensal")

    # Execução manual caso deseje gerar ranking do mês anterior
    # gerar_ranking_top10(df, modo="fechar_mes_anterior")