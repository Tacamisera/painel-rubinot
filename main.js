const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');

const { abrirChromeUmaVez, getWebSocketDebuggerUrl } = require('./chrome');
const { sleep, gerarNomeLog } = require('./utils');
const coletarDados = require('./coletarDados'); // você pode implementar ou adaptar
const coletarPerfis = require('./coletarPerfis');
const coletarMembrosGuilda = require('./coletarMembrosGuilda'); // você pode implementar ou adaptar

puppeteer.use(StealthPlugin());
const LOG_DIR = path.join(__dirname, 'logs');

let ultimaExecucaoGuilda = null;

(async () => {
  if (!fs.existsSync(LOG_DIR)) fs.mkdirSync(LOG_DIR);

  await abrirChromeUmaVez();
  const wsUrl = await getWebSocketDebuggerUrl();
  const browser = await puppeteer.connect({ browserWSEndpoint: wsUrl });

  while (true) {
    const logFile = path.join(LOG_DIR, gerarNomeLog());
    const log = fs.createWriteStream(logFile);
    const agora = new Date();

    log.write(`============================\n`);
    log.write(`🕒 Início do ciclo: ${agora.toLocaleString()}\n`);
    log.write(`============================\n`);

    try {
      await coletarDados(browser, log);      // 🧩 Coleta do ranking
      await coletarPerfis(browser, log);     // 🧬 Coleta dos perfis
     
      // Verifica horário para coletar membros da guilda
      const hora = agora.getHours();
      const minutos = agora.getMinutes();
      const dataHoje = agora.toISOString().split('T')[0];

      if (hora === 10 && minutos >= 0 && minutos <= 10 && ultimaExecucaoGuilda !== dataHoje) {
        log.write(`🏰 Iniciando coleta diária de membros da guilda...\n`);
        const page = await browser.newPage();
        await coletarMembrosGuilda(page, log);
        await page.close();
        ultimaExecucaoGuilda = dataHoje;
        log.write(`✅ Coleta de membros da guilda concluída para hoje\n`);
      }
    } catch (err) {
      log.write(`❌ Erro inesperado: ${err}\n`);
    }

    const fim = new Date();
    log.write(`⏹️ Fim do ciclo: ${fim.toLocaleString()}\n`);
    log.end();

    console.log(`⌛ Aguardando 10 minutos até o próximo ciclo...\n`);
    await sleep(600000); // 10 minutos
  }
})();