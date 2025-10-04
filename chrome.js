const { spawn } = require('child_process');
const http = require('http');

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const USER_DATA_DIR = 'C:\\Users\\iuryp\\chrome-scraper-profile';

async function abrirChromeUmaVez() {
  spawn(CHROME_PATH, [
    '--remote-debugging-port=9222',
    `--user-data-dir=${USER_DATA_DIR}`,
    '--no-first-run',
    '--no-default-browser-check'
  ], {
    detached: true,
    stdio: 'ignore'
  });
  await new Promise(r => setTimeout(r, 3000));
}

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

module.exports = { abrirChromeUmaVez, getWebSocketDebuggerUrl };