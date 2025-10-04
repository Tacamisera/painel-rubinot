// notificador.js
// Envia eventos relevantes para o Discord

const db = require('./db');
const { Client, GatewayIntentBits } = require('discord.js');
const { format } = require('date-fns');

const client = new Client({ intents: [GatewayIntentBits.Guilds] });
const DISCORD_TOKEN = process.env.DISCORD_TOKEN;
const DISCORD_CHANNEL_ID = process.env.DISCORD_CHANNEL_ID;

async function enviarNotificacoes() {
  db.all(
    `SELECT e.id AS evento_id, e.jogador_id, e.tipo, e.descricao, e.datahora, j.nome_base
     FROM eventos e
     JOIN jogadores_identidade j ON j.id = e.jogador_id
     LEFT JOIN notificacoes n ON n.evento_id = e.id
     WHERE n.id IS NULL
     ORDER BY e.datahora ASC`,
    async (err, rows) => {
      if (err) return console.error('Erro ao buscar eventos para notificação:', err);
      if (!rows.length) return console.log('🔕 Nenhuma notificação pendente.');

      const canal = await client.channels.fetch(DISCORD_CHANNEL_ID);
      if (!canal) return console.error('❌ Canal do Discord não encontrado.');

      const stmt = db.prepare(`INSERT INTO notificacoes (evento_id, enviado, data_envio) VALUES (?, 1, ?)`);
      const now = format(new Date(), 'yyyy-MM-dd HH:mm:ss');

      for (const ev of rows) {
        const mensagem = `**${ev.tipo.toUpperCase()}** • ${ev.nome_base}\n${ev.descricao} \`\`(${ev.datahora})\`\``;

        try {
          await canal.send(mensagem);
          stmt.run(ev.evento_id, now);
        } catch (e) {
          console.error('Erro ao enviar mensagem para Discord:', e);
        }
      }

      stmt.finalize(() => console.log(`✅ ${rows.length} notificações enviadas.`));
    }
  );
}

client.once('ready', () => {
  console.log(`🤖 Bot logado como ${client.user.tag}`);
  enviarNotificacoes();
});

client.login(DISCORD_TOKEN);

module.exports = enviarNotificacoes;
