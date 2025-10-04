// ===============================================================
// 🧩 DEPENDÊNCIAS E CONFIGURAÇÕES GERAIS
// ---------------------------------------------------------------
// Define bibliotecas utilizadas, caminhos e funções utilitárias
// ===============================================================

const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs');
const http = require('http');
const path = require('path');
const { spawn, spawnSync } = require('child_process');

// 🕵️‍♂️ Plugin para contornar bloqueios como Cloudflare
puppeteer.use(StealthPlugin());

// 📍 Caminhos e configurações do ambiente
const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const USER_DATA_DIR = 'C:\\Users\\iuryp\\chrome-scraper-profile';
const LOG_DIR = path.join(__dirname, 'logs');
const CSV_DIR = path.join(__dirname, 'csv');
const CSV_PATH = path.join(CSV_DIR, 'top100.csv');

// 💤 Espera de X milissegundos (delay controlado entre ciclos)
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// 🔌 Obtém a WebSocket URL para conectar com o Chrome já aberto
function getWebSocketDebuggerUrl() {
  return new Promise((resolve, reject) => {
    http.get('http://localhost:9222/json/version', res => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const json = JSON.parse(data);
          resolve(json.webSocketDebuggerUrl);
        } catch {
          reject('❌ Erro ao processar JSON da depuração.');
        }
      });
    }).on('error', () => {
      reject('❌ Chrome não está com --remote-debugging ativado.');
    });
  });
}

// 🧾 Gera nome do log baseado na data/hora atual
function gerarNomeLog() {
  const now = new Date();
  return `log_${now.getFullYear()}${String(now.getMonth()+1).padStart(2,'0')}${String(now.getDate()).padStart(2,'0')}_` +
         `${String(now.getHours()).padStart(2,'0')}${String(now.getMinutes()).padStart(2,'0')}.txt`;
}
// ===============================================================
// 🔓 ABERTURA DO CHROME COM PERFIL PERSISTENTE
// ---------------------------------------------------------------
// Inicia o Chrome uma única vez com --remote-debugging,
// permitindo o reaproveitamento da sessão entre os ciclos.
// ===============================================================

async function abrirChromeUmaVez() {
  console.log('🔒 Abrindo Chrome (mantido entre ciclos)...');

  spawn(CHROME_PATH, [
    '--remote-debugging-port=9222',
    `--user-data-dir=${USER_DATA_DIR}`,
    '--no-first-run',
    '--no-default-browser-check'
  ], {
    detached: true,
    stdio: 'ignore'
  });

  // Aguarda alguns segundos para o Chrome inicializar
  await sleep(1000);
}
// ===============================================================
// 📦 FUNÇÃO DE COLETA DOS DADOS — PÁGINAS DO RUBINOT
// ---------------------------------------------------------------
// Visita as duas páginas do TOP 100 no Rubinot, coleta os dados,
// formata as informações e salva no top100.csv com timestamp UTC
// ===============================================================

async function coletarDados(browser, log) {
  const pages = await browser.pages();
  const page = pages.length > 0 ? pages[0] : await browser.newPage();

  const timestamp = new Date().toISOString(); // UTC timestamp para cada ciclo
  const urls = [
    'https://rubinot.com.br/?subtopic=highscores&world=Elysian&category=6&currentpage=1',
    'https://rubinot.com.br/?subtopic=highscores&world=Elysian&category=6&currentpage=2'
  ];

  const resultados = [];

  for (let i = 0; i < urls.length; i++) {
    const url = urls[i];
    log.write(`🌐 Visitando página ${i + 1}...\n`);
    await page.goto(url, { waitUntil: 'domcontentloaded' });

    try {
      await page.waitForSelector('table.TableContent', { timeout: 120000 });
      log.write(`✅ Página ${i + 1} carregada\n`);
    } catch {
      log.write(`❌ Falha ao carregar página ${i + 1}\n`);
      return [];
    }

    // 🧪 Extrai os dados dos jogadores da tabela
    const jogadores = await page.evaluate(() => {
      const linhas = Array.from(document.querySelectorAll('table.TableContent tr'))
        .filter(tr => tr.bgColor === '#D4C0A1' || tr.bgColor === '#F1E0C6');

      return linhas.map(tr => {
        const tds = tr.querySelectorAll('td');
        return {
          rank: tds[0]?.innerText.trim(),
          name: tds[1]?.innerText.trim(),
          vocation: tds[2]?.innerText.trim(),
          world: tds[3]?.innerText.trim(),
          level: tds[4]?.innerText.trim(),
          points: tds[5]?.innerText.trim()
        };
      });
    });

    resultados.push(...jogadores);
    log.write(`📥 Página ${i + 1}: ${jogadores.length} registros\n`);
  }

  // 🚫 Sem resultados? Abortamos o ciclo
  if (resultados.length === 0) {
    log.write('🚫 Nenhum dado coletado.\n');
    return [];
  }

  // 💾 Constrói conteúdo CSV
  const linhas = resultados.map(j =>
    `${timestamp},"${j.rank}","${j.name}","${j.vocation}","${j.world}","${j.level}","${j.points}"`
  );
  const cabecalho = 'DataHora,Rank,Name,Vocation,World,Level,Points';
  const existe = fs.existsSync(CSV_PATH);
  const conteudo = existe
    ? linhas.join('\n') + '\n'
    : cabecalho + '\n' + linhas.join('\n') + '\n';

  fs.appendFileSync(CSV_PATH, conteudo);
  log.write(`💾 ${resultados.length} entradas salvas em top100.csv\n`);

  return resultados;
}
// ===============================================================
// 🔁 LOOP PRINCIPAL — EXECUÇÃO CÍCLICA DO SCRAPER
// ---------------------------------------------------------------
// Abre o Chrome, conecta com sessão persistente e executa:
// • Coleta de dados
// • Execução dos scripts auxiliares (ex: atualizar_csv.py)
// • Aguarda intervalo entre os ciclos
// ===============================================================

(async () => {
  // 🔐 Cria pasta de logs (se ainda não existir)
  if (!fs.existsSync(LOG_DIR)) fs.mkdirSync(LOG_DIR);
  
  // 📁 Cria pasta de csv (se ainda não existir)
  if (!fs.existsSync(CSV_DIR)) fs.mkdirSync(CSV_DIR);

  // 🧭 Inicia o Chrome com perfil persistente
  await abrirChromeUmaVez();

  // 🔌 Conecta ao Chrome via WebSocket (devtools)
  const wsUrl = await getWebSocketDebuggerUrl();
  const browser = await puppeteer.connect({ browserWSEndpoint: wsUrl });

  // 🔁 Loop infinito: coleta + scripts + espera
  while (true) {
    const logFile = path.join(LOG_DIR, gerarNomeLog());
    const log = fs.createWriteStream(logFile);
    const agora = new Date();

    log.write(`============================\n`);
    log.write(`🕒 Início do ciclo: ${agora.toLocaleString()}\n`);
    log.write(`============================\n`);

    try {
      await coletarDados(browser, log);

      // ▶️ Executa atualizar_csv.py
      log.write('🔄 Executando atualizar_csv.py...\n');
      const atualizar = spawnSync('python', ['atualizar_csv.py'], { encoding: 'utf-8' });
      if (atualizar.error) {
        log.write(`❌ Erro ao executar atualizar_csv.py: ${atualizar.error.message}\n`);
      } else {
        log.write(`📤 atualizar_csv.py executado com sucesso\n`);
        log.write(atualizar.stdout || '');
        log.write(atualizar.stderr || '');
      }

      // ▶️ Executa destaques.py (Discord)
      log.write('📣 Executando destaques.py...\n');
      const destaques = spawnSync('python', ['destaques.py'], { encoding: 'utf-8' });
      if (destaques.error) {
        log.write(`❌ Erro ao executar destaques.py: ${destaques.error.message}\n`);
      } else {
        log.write(`📢 destaques.py executado com sucesso\n`);
        log.write(destaques.stdout || '');
        log.write(destaques.stderr || '');
      }

    } catch (err) {
      log.write(`❌ Erro inesperado: ${err}\n`);
    }

    const fim = new Date();
    log.write(`⏹️ Fim do ciclo: ${fim.toLocaleString()}\n\n`);
    log.end();

    console.log(`⌛ Aguardando 10 minutos até o próximo ciclo...\n`);
    await sleep(600000); // 10 minutos
  }
})();