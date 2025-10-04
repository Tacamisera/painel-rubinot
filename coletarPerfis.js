const db = require('./db');
const { getTimestampUTC3, sleep } = require('./utils');
const fs = require('fs');
const path = require('path');

// Função utilitária para inserir nome anterior
async function inserirNomeAnterior(jogador_id, nome, datahora) {
  return new Promise((resolve, reject) => {
    db.run(
      `INSERT INTO nomes_anteriores (jogador_id, nome, datahora) VALUES (?, ?, ?)`,
      [jogador_id, nome, datahora],
      err => (err ? reject(err) : resolve())
    );
  });
}

// Função utilitária para inserir histórico de guilda
async function inserirHistoricoGuilda(jogador_id, guilda_id, datahora) {
  return new Promise((resolve, reject) => {
    db.run(
      `INSERT INTO historico_guilda (jogador_id, guilda_id, datahora) VALUES (?, ?, ?)`,
      [jogador_id, guilda_id, datahora],
      err => (err ? reject(err) : resolve())
    );
  });
}

// Função utilitária para inserir/obter guilda
async function obterOuCriarGuilda(nome, url) {
  if (!nome) return null;
  return new Promise((resolve, reject) => {
    db.get(`SELECT id FROM guildas WHERE nome = ?`, [nome], (err, row) => {
      if (err) return reject(err);
      if (row) return resolve(row.id);
      db.run(
        `INSERT INTO guildas (nome, url) VALUES (?, ?)`,
        [nome, url],
        function (err2) {
          if (err2) return reject(err2);
          resolve(this.lastID);
        }
      );
    });
  });
}

// Função utilitária para inserir/atualizar jogador
async function inserirOuAtualizarJogador(dados, guilda_id) {
  return new Promise((resolve, reject) => {
    db.get(
      `SELECT id FROM jogadores_identidade WHERE nome_base = ? AND world = ?`,
      [dados.personagem_atual, dados.world],
      (err, row) => {
        if (err) return reject(err);
        if (row) {
          db.run(
            `UPDATE jogadores_identidade SET 
              titulo = ?, vocation = ?, guilda_id = ?, ultima_coleta = ?
             WHERE id = ?`,
            [
              '', // título não coletado aqui
              dados.vocation,
              guilda_id,
              dados.ultima_coleta,
              row.id
            ],
            err2 => (err2 ? reject(err2) : resolve(row.id))
          );
        } else {
          db.run(
            `INSERT INTO jogadores_identidade 
              (nome_base, titulo, vocation, world, guilda_id, ultima_coleta)
             VALUES (?, ?, ?, ?, ?, ?)`,
            [
              dados.personagem_atual,
              '', // título não coletado aqui
              dados.vocation,
              dados.world,
              guilda_id,
              dados.ultima_coleta
            ],
            function (err2) {
              if (err2) return reject(err2);
              resolve(this.lastID);
            }
          );
        }
      }
    );
  });
}

async function coletarPerfis(browser, log) {
  const page = await browser.newPage();
  log.write(`📣 Iniciando coleta de perfis individuais ainda não processados...\n`);

  // 1. Buscar todos os nomes únicos do highscores que ainda não existem em jogadores_identidade
  const nomesParaRaspar = await new Promise((resolve, reject) => {
    db.all(
      `SELECT DISTINCT name, vocation, world
         FROM highscores
        WHERE name NOT IN (
          SELECT nome_base FROM jogadores_identidade
        )`,
      (err, rows) => (err ? reject(err) : resolve(rows))
    );
  });

  if (!nomesParaRaspar.length) {
    log.write('⚠️ Nenhum personagem novo para raspar.\n');
    await page.close();
    return;
  }

  log.write(`🔎 ${nomesParaRaspar.length} personagens para raspagem individual\n`);

  // CSV setup
  const csvPath = path.join(__dirname, 'export_perfis.csv');
  const csvHeader = [
    'personagem_atual',
    'nomes_anteriores',
    'vocation',
    'world',
    'guild',
    'guild_url',
    'ultima_coleta'
  ].join(';') + '\n';

  // Se o arquivo não existe, cria com cabeçalho
  if (!fs.existsSync(csvPath)) {
    fs.writeFileSync(csvPath, csvHeader, 'utf8');
  }

  for (const jogador of nomesParaRaspar) {
    const nome = jogador.name;
    const url = `https://rubinot.com.br/?subtopic=characters&name=${encodeURIComponent(nome)}`;

    try {
      log.write(`🔍 Coletando perfil: ${nome}\n`);
      await page.goto(url, { waitUntil: 'domcontentloaded' });
      await page.waitForSelector('table.TableContent', { timeout: 180000 });

      // Extração robusta dos dados do personagem
      const dados = await page.evaluate(() => {
        const table = document.querySelector('.TableContent');
        if (!table) {
          return {
            personagem_atual: '',
            nomes_anteriores: [],
            vocation: '',
            world: '',
            guild: '',
            guild_url: ''
          };
        }

        const linhas = Array.from(table.querySelectorAll('tr'));
        let personagem_atual = '';
        let nomes_anteriores = [];
        let vocation = '';
        let world = '';
        let guild = '';
        let guild_url = '';

        for (const tr of linhas) {
          const tds = tr.querySelectorAll('td');
          if (tds.length < 2) continue;
          const label = tds[0].innerText.replace(':', '').trim();
          const valor = tds[1].innerText.trim();

          if (label === 'Name') {
            const b = tds[1].querySelector('b');
            personagem_atual = b ? b.innerText.trim() : valor;
          }
          if (label === 'Former Names') {
            const spans = tds[1].querySelectorAll('span');
            nomes_anteriores = Array.from(spans).map(s => s.innerText.trim());
            if (!nomes_anteriores.length && valor) nomes_anteriores = [valor];
          }
          if (label === 'Vocation') {
            vocation = valor;
          }
          if (label === 'World') {
            world = valor;
          }
          if (label === 'Guild') {
            const link = tds[1].querySelector('a[href*="subtopic=guilds"]');
            guild = link ? link.innerText.trim() : valor.replace(/^the Leader of the |a Member of the /, '').trim();
            guild_url = link ? link.href : '';
          }
        }

        return {
          personagem_atual,
          nomes_anteriores,
          vocation,
          world,
          guild,
          guild_url
        };
      });

      dados.ultima_coleta = getTimestampUTC3();

      // 1. Guilda
      const guilda_id = await obterOuCriarGuilda(dados.guild, dados.guild_url);

      // 2. Jogador
      const jogador_id = await inserirOuAtualizarJogador(dados, guilda_id);

      // 3. Nomes anteriores
      for (const nomeAnt of dados.nomes_anteriores) {
        await inserirNomeAnterior(jogador_id, nomeAnt, dados.ultima_coleta);
      }

      // 4. Histórico de guilda
      if (guilda_id) {
        await inserirHistoricoGuilda(jogador_id, guilda_id, dados.ultima_coleta);
      }

      // 5. Salva no CSV
      const csvLine = [
        `"${dados.personagem_atual.replace(/"/g, '""')}"`,
        `"${dados.nomes_anteriores.join(', ').replace(/"/g, '""')}"`,
        `"${dados.vocation.replace(/"/g, '""')}"`,
        `"${dados.world.replace(/"/g, '""')}"`,
        `"${(dados.guild || '').replace(/"/g, '""')}"`,
        `"${(dados.guild_url || '').replace(/"/g, '""')}"`,
        `"${dados.ultima_coleta}"`
      ].join(';') + '\n';
      fs.appendFileSync(csvPath, csvLine, 'utf8');

      log.write(`✅ Perfil atualizado e exportado: ${dados.personagem_atual}\n`);
      await sleep(1000);

    } catch (err) {
      log.write(`❌ Falha no perfil de ${nome}: ${err.message}\n`);
    }
  }

  log.write(`📌 Coleta de perfis individuais finalizada\n`);
  await page.close();
}

module.exports = coletarPerfis;