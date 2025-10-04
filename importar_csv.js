const fs = require('fs');
const path = require('path');
const sqlite3 = require('sqlite3').verbose();
const csv = require('csv-parser');

// 📂 Caminho para o CSV
const CSV_PATH = path.join(__dirname, 'top100.csv');

// 🔌 Conexão com SQLite
const db = new sqlite3.Database('top100.db');

// 🕒 Converte timestamp UTC para UTC-3 (horário de Brasília)
function converterParaUTC3(utcStr) {
  const dataUTC = new Date(utcStr);
  return dataUTC.toLocaleString('sv-SE', {
    timeZone: 'America/Sao_Paulo',
    hour12: false
  }).replace(' ', 'T'); // Ex: 2025-06-28T18:16:02
}

// 🧱 Criação da tabela de testes
db.serialize(() => {
  db.run(`DROP TABLE IF EXISTS TOP100`);
  db.run(`
    CREATE TABLE TOP100 (
      datahora TEXT,
      rank INTEGER,
      name TEXT,
      vocation TEXT,
      world TEXT,
      level INTEGER,
      points INTEGER
    );
  `);
});

// 📥 Leitura do CSV e inserção no banco
fs.createReadStream(CSV_PATH)
  .pipe(csv())
  .on('data', (row) => {
    const dataConvertida = converterParaUTC3(row.DataHora);

    const query = `
      INSERT INTO TOP100 (
        datahora, rank, name, vocation, world, level, points
      ) VALUES (?, ?, ?, ?, ?, ?, ?)
    `;

    db.run(query, [
      dataConvertida,
      parseInt(row.Rank),
      row.Name,
      row.Vocation,
      row.World,
      parseInt(row.Level),
      parseInt(row.Points)
    ]);
  })
  .on('end', () => {
    console.log('✅ Importação concluída com horário ajustado para UTC-3!');
    db.close();
  });