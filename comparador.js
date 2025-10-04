// comparador.js
// Detecta mudanças entre a coleta atual e a anterior e gera eventos

const db = require('./db');
const { format } = require('date-fns');

function getUltimoSnapshot(callback) {
  db.all(
    `SELECT DISTINCT datahora FROM highscores ORDER BY datahora DESC LIMIT 2`,
    (err, rows) => {
      if (err) return callback(err);
      if (rows.length < 2) return callback(null, null); // nada para comparar
      const [current, previous] = rows.map((r) => r.datahora);
      callback(null, { atual: current, anterior: previous });
    }
  );
}

function compararSnapshots({ atual, anterior }, callback) {
  const jogadores = {};
  const eventos = [];

  db.all(
    `SELECT h.*, j.nome_base, j.guild_nome
     FROM highscores h
     LEFT JOIN jogadores_identidade j ON j.id = h.jogador_id
     WHERE h.datahora IN (?, ?)`,
    [atual, anterior],
    (err, rows) => {
      if (err) return callback(err);

      // Agrupar por jogador e snapshot
      for (const row of rows) {
        const key = row.jogador_id || row.name;
        if (!jogadores[key]) jogadores[key] = {};
        jogadores[key][row.datahora] = row;
      }

      // Comparar atual vs anterior
      for (const key in jogadores) {
        const atualData = jogadores[key][atual];
        const anteriorData = jogadores[key][anterior];

        if (!anteriorData && atualData) {
          eventos.push({ jogador_id: atualData.jogador_id, tipo: 'entrou_top1000', descricao: `Entrou no top 1000 na posição ${atualData.rank}` });
        } else if (anteriorData && !atualData) {
          eventos.push({ jogador_id: anteriorData.jogador_id, tipo: 'saiu_top1000', descricao: `Saiu do top 1000 (estava na posição ${anteriorData.rank})` });
        } else if (anteriorData && atualData) {
          if (anteriorData.level !== atualData.level) {
            eventos.push({ jogador_id: atualData.jogador_id, tipo: 'level_up', descricao: `Level ${anteriorData.level} → ${atualData.level}` });
          }
          if (anteriorData.rank !== atualData.rank) {
            eventos.push({ jogador_id: atualData.jogador_id, tipo: 'rank_change', descricao: `Rank ${anteriorData.rank} → ${atualData.rank}` });
          }
          if (anteriorData.name !== atualData.name) {
            eventos.push({ jogador_id: atualData.jogador_id, tipo: 'rename', descricao: `Renomeado de ${anteriorData.name} para ${atualData.name}` });
          }
          if (anteriorData.guild_nome !== atualData.guild_nome) {
            eventos.push({ jogador_id: atualData.jogador_id, tipo: 'guild_change', descricao: `Guilda de '${anteriorData.guild_nome}' para '${atualData.guild_nome}'` });
          }
        }
      }

      callback(null, eventos);
    }
  );
}

function registrarEventos(eventos, callback) {
  const now = format(new Date(), "yyyy-MM-dd HH:mm:ss");
  const stmt = db.prepare(`INSERT INTO eventos (jogador_id, tipo, descricao, datahora) VALUES (?, ?, ?, ?)`);

  for (const ev of eventos) {
    stmt.run(ev.jogador_id, ev.tipo, ev.descricao, now);
  }
  stmt.finalize(callback);
}

function executarComparacao() {
  getUltimoSnapshot((err, range) => {
    if (err || !range) return console.error('Erro ao obter snapshots:', err);
    compararSnapshots(range, (err, eventos) => {
      if (err) return console.error('Erro ao comparar snapshots:', err);
      if (!eventos.length) return console.log('Nenhuma mudança detectada.');
      registrarEventos(eventos, () => console.log(`✅ ${eventos.length} eventos registrados.`));
    });
  });
}

module.exports = executarComparacao;
