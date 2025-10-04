const http = require('http');

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function getTimestampUTC3() {
  return new Date().toLocaleString('sv-SE', {
    timeZone: 'America/Sao_Paulo',
    hour12: false
  }).replace(' ', 'T');
}

function gerarNomeLog() {
  const now = new Date();
  return `log_${now.getFullYear()}${String(now.getMonth()+1).padStart(2,'0')}${String(now.getDate()).padStart(2,'0')}_` +
         `${String(now.getHours()).padStart(2,'0')}${String(now.getMinutes()).padStart(2,'0')}.txt`;
}

module.exports = { sleep, getTimestampUTC3, gerarNomeLog };