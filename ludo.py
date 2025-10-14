"""
ludo.py
Mini Ludo module for Pyrogram-based Telegram bot.

Integration:
1. Put this file in your repo root (next to your bot's main file).
2. In your bot's main file (where Client(...) is created), add:

   from ludo import init_ludo
   init_ludo(app)

3. Restart your bot.

Commands:
/start_ludo, /join_ludo, /leave_ludo, /begin_ludo, /roll, /board, /end_ludo

This module stores game state in `ludo_games.json` in repo root. If you prefer DB (Mongo/Redis), replace save/load functions.
"""

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler
import asyncio, json, os

DATA_FILE = "ludo_games.json"
BOARD_SIZE = 30

games = {}               # chat_id -> LudoGame
games_lock = asyncio.Lock()

class LudoGame:
    def __init__(self, chat_id: int):
        self.chat_id = chat_id
        self.players = []          # list of {'id':int,'name':str}
        self.positions = {}        # user_id(int) -> pos (int) or -1 for not entered
        self.turn_index = 0
        self.started = False
        self.lock = asyncio.Lock()

# --- small helpers for thread-safe file I/O ---

def _sync_write_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f)

def _sync_read_json(path):
    with open(path) as f:
        return json.load(f)

async def save_all_games():
    async with games_lock:
        data = {}
        for cid, g in games.items():
            data[str(cid)] = {
                'players': [{'id': p['id'], 'name': p['name']} for p in g.players],
                'positions': {str(k): v for k, v in g.positions.items()},
                'turn_index': g.turn_index,
                'started': g.started
            }
        await asyncio.to_thread(_sync_write_json, DATA_FILE, data)

async def load_all_games():
    if not os.path.exists(DATA_FILE):
        return
    data = await asyncio.to_thread(_sync_read_json, DATA_FILE)
    async with games_lock:
        for cid_str, gdata in data.items():
            try:
                cid = int(cid_str)
            except:
                continue
            g = LudoGame(cid)
            g.players = [{'id': int(p['id']), 'name': p['name']} for p in gdata.get('players', [])]
            g.positions = {int(k): v for k, v in gdata.get('positions', {}).items()}
            g.turn_index = gdata.get('turn_index', 0)
            g.started = gdata.get('started', False)
            games[cid] = g

# Human-friendly board formatter

def format_board_text(game: LudoGame) -> str:
    lines = []
    lines.append(f"📋 Ludo Board — players: {len(game.players)} — Turn idx: {game.turn_index}")
    for idx, p in enumerate(game.players):
        uid = p['id']
        name = p['name']
        pos = game.positions.get(uid, -1)
        if pos == -1:
            status = "🏁 Not entered"
            bar = "[----------]"
        else:
            percent = max(0, min(10, int((pos / BOARD_SIZE) * 10)))
            bar = "[" + "●"*percent + "-"*(10-percent) + "]"
            status = f"{pos}/{BOARD_SIZE}"
        turn_marker = " ← current" if idx == game.turn_index and game.started else ""
        lines.append(f"{name} — {status} {bar}{turn_marker}")
    return "\n".join(lines)

# Entry function to attach handlers to your Client

def init_ludo(app: Client):
    @app.on_connect()
    async def _on_connect(client):
        await load_all_games()

    async def cmd_start_ludo(client: Client, message: Message):
        chat_id = message.chat.id
        async with games_lock:
            if chat_id in games and games[chat_id].started:
                await message.reply("⚠️ A game is already running in this chat.")
                return
            games[chat_id] = LudoGame(chat_id)
        await save_all_games()
        await message.reply("🎮 Ludo game created! Type /join_ludo to join. When all players joined, use /begin_ludo to start.")

    async def cmd_join_ludo(client: Client, message: Message):
        chat_id = message.chat.id
        user = message.from_user
        async with games_lock:
            if chat_id not in games:
                await message.reply("No active Ludo game. Use /start_ludo to create one.")
                return
            game = games[chat_id]
        async with game.lock:
            if any(p['id'] == user.id for p in game.players):
                await message.reply("You're already in the game.")
                return
            game.players.append({'id': user.id, 'name': user.first_name})
            game.positions[user.id] = -1
        await save_all_games()
        await message.reply(f"✅ {user.first_name} joined the Ludo game! Total players: {len(game.players)}")

    async def cmd_leave_ludo(client: Client, message: Message):
        chat_id = message.chat.id
        user = message.from_user
        async with games_lock:
            if chat_id not in games:
                await message.reply("No active Ludo game.")
                return
            game = games[chat_id]
        async with game.lock:
            removed = False
            for i,p in enumerate(game.players):
                if p['id'] == user.id:
                    removed = True
                    del game.players[i]
                    game.positions.pop(user.id, None)
                    if i <= game.turn_index and game.turn_index>0:
                        game.turn_index -= 1
                    break
            if not removed:
                await message.reply("You're not in the game.")
                return
            if len(game.players) == 0:
                async with games_lock:
                    try:
                        del games[chat_id]
                    except KeyError:
                        pass
                await save_all_games()
                await message.reply("You left. No players remain — game ended.")
                return
        await save_all_games()
        await message.reply(f"{user.first_name} left the game. Players remaining: {len(game.players)}")

    async def cmd_begin_ludo(client: Client, message: Message):
        chat_id = message.chat.id
        async with games_lock:
            if chat_id not in games:
                await message.reply("No active Ludo game. Use /start_ludo to create one.")
                return
            game = games[chat_id]
        async with game.lock:
            if game.started:
                await message.reply("Game already started.")
                return
            if len(game.players) < 2:
                await message.reply("Need at least 2 players to start.")
                return
            game.started = True
            game.turn_index = 0
        await save_all_games()
        starter = game.players[game.turn_index]['name']
        await message.reply(f"🏁 Game started! {starter} goes first. Use /roll to roll the dice on your turn.\n\n" + format_board_text(game))

    async def cmd_roll(client: Client, message: Message):
        chat_id = message.chat.id
        user = message.from_user
        async with games_lock:
            if chat_id not in games:
                await message.reply("No active Ludo game. Use /start_ludo to create one.")
                return
            game = games[chat_id]
        async with game.lock:
            if not game.started:
                await message.reply("Game hasn't started yet. Use /begin_ludo.")
                return
            if game.players[game.turn_index]['id'] != user.id:
                await message.reply("Wait for your turn. Current player: " + game.players[game.turn_index]['name'])
                return
        dice_msg = await message.reply_dice(emoji="🎲")
        dice_value = dice_msg.dice.value
        async with game.lock:
            uid = user.id
            pos = game.positions.get(uid, -1)
            extra_turn = False
            captured_player = None
            moved = False
            winner = None
            if pos == -1:
                if dice_value == 6:
                    game.positions[uid] = 0
                    moved = True
                    extra_turn = True
                else:
                    moved = False
                    extra_turn = False
            else:
                newpos = pos + dice_value
                if newpos > BOARD_SIZE:
                    moved = False
                    extra_turn = (dice_value == 6)
                elif newpos == BOARD_SIZE:
                    game.positions[uid] = newpos
                    moved = True
                    winner = user
                    game.started = False
                else:
                    game.positions[uid] = newpos
                    moved = True
                    extra_turn = (dice_value == 6)
            if moved and winner is None:
                for p in game.players:
                    pid = p['id']
                    if pid != uid and game.positions.get(pid, -1) == game.positions.get(uid, -1) and game.positions.get(uid, -1) != -1:
                        game.positions[pid] = -1
                        captured_player = p['name']
            if winner is None and not extra_turn:
                game.turn_index = (game.turn_index + 1) % len(game.players) if len(game.players)>0 else 0
            if winner is not None:
                wname = winner.first_name
                async with games_lock:
                    try:
                        del games[chat_id]
                    except KeyError:
                        pass
                await save_all_games()
                await message.reply(f"🎉 {wname} has reached home and won the Ludo game! Congratulations!")
                return
            await save_all_games()
            status = f"🎲 {user.first_name} rolled {dice_value}.\n"
            if moved:
                status += f"➡️ Moved to {game.positions.get(uid)}.\n"
            else:
                status += "✋ Can't move this turn.\n"
            if captured_player:
                status += f"💥 Captured {captured_player}! They return to start.\n"
            if extra_turn:
                status += f"🔁 You rolled a 6, go again!\n"
                next_player = user.first_name
            else:
                next_player = game.players[game.turn_index]['name']
                status += f"⏭️ Next: {next_player}\n"
            status += "\n" + format_board_text(game)
        await message.reply(status)

    async def cmd_board(client: Client, message: Message):
        chat_id = message.chat.id
        async with games_lock:
            if chat_id not in games:
                await message.reply("No active Ludo game.")
                return
            game = games[chat_id]
        async with game.lock:
            await message.reply(format_board_text(game))

    async def cmd_end_ludo(client: Client, message: Message):
        chat_id = message.chat.id
        async with games_lock:
            if chat_id in games:
                del games[chat_id]
                await save_all_games()
                await message.reply("🛑 Ludo game ended and removed.")
                return
            else:
                await message.reply("No active Ludo game to end.")

    # register handlers
    app.add_handler(MessageHandler(cmd_start_ludo, filters=filters.command("start_ludo")))
    app.add_handler(MessageHandler(cmd_join_ludo, filters=filters.command("join_ludo")))
    app.add_handler(MessageHandler(cmd_leave_ludo, filters=filters.command("leave_ludo")))
    app.add_handler(MessageHandler(cmd_begin_ludo, filters=filters.command("begin_ludo")))
    app.add_handler(MessageHandler(cmd_roll, filters=filters.command("roll")))
    app.add_handler(MessageHandler(cmd_board, filters=filters.command("board")))
    app.add_handler(MessageHandler(cmd_end_ludo, filters=filters.command("end_ludo")))

    return
