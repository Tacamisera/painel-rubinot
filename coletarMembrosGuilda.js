const db = require('./db');
const { sleep } = require('./utils');

// Função utilitária para inserir membros na tabela guildas_membros
async function inserirMembroGuilda(guilda_id, membro) {
  return new Promise((resolve, reject) => {
    db.run(
      `INSERT INTO guildas_membros (guilda_id, membro_nome, membro_titulo, vocation, level, joined)
       VALUES (?, ?, ?, ?, ?, ?)`,
      [
        guilda_id,
        membro.membro_nome,
        membro.membro_titulo,
        membro.vocation,
        membro.level,
        membro.joined
      ],
      err => (err ? reject(err) : resolve())
    );
  });
}

// Função principal: coleta membros de todas as guildas registradas
// Recebe uma instância de page já aberta e log
async function coletarMembrosGuildas(page, log) {
  // 1. Buscar todas as guildas registradas no banco
  const guildas = await new Promise((resolve, reject) => {
    db.all(`SELECT id, nome FROM guildas`, (err, rows) => {
      if (err) reject(err);
      else resolve(rows);
    });
  });

  if (!guildas.length) {
    log.write('⚠️ Nenhuma guilda registrada no banco.\n');
    return;
  }

  for (const guilda of guildas) {
    try {
      // Monta a URL da guilda conforme padrão do RubinOT
      const guildNameUrl = encodeURIComponent(guilda.nome.replace(/ /g, '+'));
      const url = `https://rubinot.com.br/?subtopic=guilds&page=view&GuildName=${guildNameUrl}`;

      log.write(`🛡️ Coletando membros da guilda ${guilda.nome}\n`);
      await page.goto(url, { waitUntil: 'domcontentloaded' });
      await page.waitForSelector('table.TableContent', { timeout: 60000 });

      // Coleta robusta dos membros da guilda
      const membros = await page.evaluate(() => {
        // Seleciona todas as linhas da tabela de membros, ignorando cabeçalho
        const rows = Array.from(document.querySelectorAll('table.TableContent tr')).filter(tr => {
          // Garante que a linha tem pelo menos 5 colunas (evita cabeçalho)
          return tr.querySelectorAll('td').length >= 5;
        });

        return rows.map(tr => {
          const tds = tr.querySelectorAll('td');
          // Nome e título
          let membro_nome = '';
          let membro_titulo = '';
          const link = tds[1]?.querySelector('a');
          if (link) {
            membro_nome = link.innerText.trim();
            // Título entre parênteses, se existir
            const tituloMatch = tds[1].innerText.match(/\((.*?)\)/);
            if (tituloMatch) {
              membro_titulo = tituloMatch[1].trim();
            }
          }
          return {
            membro_nome,
            membro_titulo,
            vocation: tds[2]?.innerText.trim() || '',
            level: parseInt(tds[3]?.innerText.trim() || '0'),
            joined: tds[4]?.innerText.trim() || ''
          };
        }).filter(m => m.membro_nome);
      });

      // Limpa membros antigos da guilda antes de inserir os novos
      await new Promise((resolve, reject) => {
        db.run(`DELETE FROM guildas_membros WHERE guilda_id = ?`, [guilda.id], err => (err ? reject(err) : resolve()));
      });

      for (const membro of membros) {
        await inserirMembroGuilda(guilda.id, membro);
      }

      log.write(`✅ ${membros.length} membros registrados para ${guilda.nome}\n`);
      await sleep(1000);

    } catch (err) {
      log.write(`❌ Erro ao coletar membros da guilda ${guilda.nome}: ${err.message}\n`);
    }
  }
}

module.exports = coletarMembrosGuildas;