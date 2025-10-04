const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const dbPath = path.join(__dirname, 'rubinot.db');
const db = new sqlite3.Database(dbPath, (err) => {
  if (err) return console.error('❌ Erro ao conectar no banco:', err.message);
  console.log('💾 Banco local SQLite conectado com sucesso');
});

db.serialize(() => {
  // 🏰 Guildas (normalização)
  db.run(`
    CREATE TABLE IF NOT EXISTS guildas (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      nome TEXT NOT NULL UNIQUE,
      url TEXT DEFAULT NULL
    )
  `);
  db.run(`CREATE INDEX IF NOT EXISTS guildas_nome_idx ON guildas(nome)`);

  // 📊 Histórico de rankings por snapshot
  db.run(`
    CREATE TABLE IF NOT EXISTS coletas (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      datahora TEXT NOT NULL,
      tipo TEXT DEFAULT 'auto' -- ou 'manual'
    )
  `);
  db.run(`CREATE INDEX IF NOT EXISTS coletas_datahora_idx ON coletas(datahora)`);

  db.run(`
    CREATE TABLE IF NOT EXISTS highscores (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      coleta_id INTEGER NOT NULL,
      datahora TEXT NOT NULL,
      rank INTEGER NOT NULL,
      name TEXT NOT NULL,
      vocation TEXT NOT NULL DEFAULT '',
      world TEXT NOT NULL DEFAULT '',
      level INTEGER NOT NULL,
      points INTEGER NOT NULL,
      jogador_id INTEGER,
      FOREIGN KEY (coleta_id) REFERENCES coletas(id),
      FOREIGN KEY (jogador_id) REFERENCES jogadores_identidade(id)
    )
  `);
  db.run(`CREATE INDEX IF NOT EXISTS highscores_datahora_idx ON highscores(datahora)`);
  db.run(`CREATE INDEX IF NOT EXISTS highscores_name_idx     ON highscores(name)`);
  db.run(`CREATE INDEX IF NOT EXISTS highscores_rank_idx     ON highscores(rank)`);
  db.run(`CREATE INDEX IF NOT EXISTS highscores_world_idx    ON highscores(world)`);

  // 🧬 Identidade persistente de jogadores
  db.run(`
    CREATE TABLE IF NOT EXISTS jogadores_identidade (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      nome_base TEXT NOT NULL,
      titulo TEXT DEFAULT '',
      vocation TEXT NOT NULL DEFAULT '',
      world TEXT NOT NULL DEFAULT '',
      guilda_id INTEGER DEFAULT NULL,
      ultima_coleta TEXT NOT NULL,
      discord_id TEXT DEFAULT NULL,
      FOREIGN KEY (guilda_id) REFERENCES guildas(id)
    )
  `);
  db.run(`CREATE INDEX IF NOT EXISTS identidade_nome_idx ON jogadores_identidade(nome_base)`);
  db.run(`CREATE INDEX IF NOT EXISTS identidade_world_idx ON jogadores_identidade(world)`);
  db.run(`CREATE INDEX IF NOT EXISTS identidade_guilda_idx ON jogadores_identidade(guilda_id)`);

  // 🧾 Histórico de nomes anteriores (normalizado)
  db.run(`
    CREATE TABLE IF NOT EXISTS nomes_anteriores (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      jogador_id INTEGER NOT NULL,
      nome TEXT NOT NULL,
      datahora TEXT NOT NULL,
      FOREIGN KEY (jogador_id) REFERENCES jogadores_identidade(id)
    )
  `);
  db.run(`CREATE INDEX IF NOT EXISTS nomes_jogador_idx ON nomes_anteriores(jogador_id)`);
  db.run(`CREATE INDEX IF NOT EXISTS nomes_nome_idx ON nomes_anteriores(nome)`);

  // 🛡️ Histórico de guildas por jogador
  db.run(`
    CREATE TABLE IF NOT EXISTS historico_guilda (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      jogador_id INTEGER NOT NULL,
      guilda_id INTEGER NOT NULL,
      datahora TEXT NOT NULL,
      FOREIGN KEY (jogador_id) REFERENCES jogadores_identidade(id),
      FOREIGN KEY (guilda_id) REFERENCES guildas(id)
    )
  `);
  db.run(`CREATE INDEX IF NOT EXISTS hist_guilda_guilda_idx    ON historico_guilda(guilda_id)`);
  db.run(`CREATE INDEX IF NOT EXISTS hist_guilda_jogador_idx ON historico_guilda(jogador_id)`);
  db.run(`CREATE INDEX IF NOT EXISTS hist_guilda_data_idx    ON historico_guilda(datahora)`);

  // 👥 Snapshot de membros da guilda
  db.run(`
    CREATE TABLE IF NOT EXISTS guildas_membros (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      guilda_id INTEGER NOT NULL,
      membro_nome TEXT NOT NULL,
      membro_titulo TEXT DEFAULT '',
      vocation TEXT NOT NULL DEFAULT '',
      level INTEGER NOT NULL,
      joined TEXT NOT NULL,
      FOREIGN KEY (guilda_id) REFERENCES guildas(id)
    )
  `);
  db.run(`CREATE INDEX IF NOT EXISTS membros_guilda_idx ON guildas_membros(guilda_id)`);
  db.run(`CREATE INDEX IF NOT EXISTS membros_nome_idx  ON guildas_membros(membro_nome)`);

  // 📈 Registro de eventos importantes
  db.run(`
    CREATE TABLE IF NOT EXISTS eventos (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      jogador_id INTEGER NOT NULL,
      guilda_id INTEGER DEFAULT NULL,
      tipo TEXT NOT NULL, -- ex: level_up, rename, death, rank_change
      descricao TEXT NOT NULL,
      datahora TEXT NOT NULL,
      FOREIGN KEY (jogador_id) REFERENCES jogadores_identidade(id),
      FOREIGN KEY (guilda_id) REFERENCES guildas(id)
    )
  `);
  db.run(`CREATE INDEX IF NOT EXISTS eventos_tipo_idx ON eventos(tipo)`);
  db.run(`CREATE INDEX IF NOT EXISTS eventos_data_idx ON eventos(datahora)`);

  // 🔔 Tabela de notificações para integração com Discord
  db.run(`
    CREATE TABLE IF NOT EXISTS notificacoes (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      evento_id INTEGER NOT NULL,
      enviado INTEGER DEFAULT 0,
      data_envio TEXT DEFAULT NULL,
      FOREIGN KEY (evento_id) REFERENCES eventos(id)
    )
  `);
});

module.exports = db;
