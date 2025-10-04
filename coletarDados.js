const db = require('./db');
const { getTimestampUTC3, sleep } = require('./utils');

/**
 * Cria uma nova coleta e retorna o id gerado.
 */
function criarColeta(datahora, tipo = 'auto') {
  return new Promise((resolve, reject) => {
    db.run(
      `INSERT INTO coletas (datahora, tipo) VALUES (?, ?)`,
      [datahora, tipo],
      function (err) {
        if (err) return reject(err);
        resolve(this.lastID);
      }
    );
  });
}

async function coletarDados(browser, log) {
  const page = await browser.newPage();
  const timestamp = getTimestampUTC3();
  let totalJogadores = 0;

  // Cria a coleta e obtém o coleta_id
  let coletaId;
  try {
    coletaId = await criarColeta(timestamp, 'auto');
  } catch (err) {
    log.write(`❌ Erro ao criar registro de coleta: ${err.message}\n`);
    await page.close();
    return;
  }

  for (let pagina = 1; pagina <= 20; pagina++) {
    const url = `https://rubinot.com.br/?subtopic=highscores&world=Elysian&beprotection=-1&category=6&profession=0&currentpage=${pagina}`;
    log.write(`🚀 Coletando página ${pagina}: ${url}\n`);

    try {
      await page.goto(url, { waitUntil: 'domcontentloaded' });
      await page.waitForSelector('table.TableContent', { timeout: 180000 });

      const jogadores = await page.evaluate(() => {
        const rows = Array.from(document.querySelectorAll('table.TableContent tr')).slice(1);

        return rows.map(tr => {
          const tds = tr.querySelectorAll('td');
          return {
            rank: parseInt(tds[0]?.innerText.trim()),
            name: tds[1]?.innerText.trim(),
            vocation: tds[2]?.innerText.trim(),
            world: tds[3]?.innerText.trim(),
            level: parseInt(tds[4]?.innerText.trim()),
            points: parseInt(tds[5]?.innerText.trim())
          };
        }).filter(j => j.name);
      });

      const stmt = db.prepare(`
        INSERT INTO highscores (
          coleta_id, datahora, rank, name, vocation, world, level, points
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
      `);

      for (const jogador of jogadores) {
        stmt.run([
          coletaId,
          timestamp,
          jogador.rank,
          jogador.name,
          jogador.vocation,
          jogador.world,
          jogador.level,
          jogador.points
        ]);
        totalJogadores++;
      }

      stmt.finalize();
      log.write(`✅ Página ${pagina}: ${jogadores.length} jogadores inseridos\n`);
      await sleep(800);

    } catch (err) {
      log.write(`❌ Erro na página ${pagina}: ${err.message}\n`);
    }
  }

  await page.close();
  log.write(`📊 Total final de jogadores coletados: ${totalJogadores}\n`);
}

module.exports = coletarDados;