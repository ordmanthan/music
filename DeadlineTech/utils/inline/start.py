# premium_start_system.py
# Copy-paste ready — drop into your handlers folder (e.g., handlers/premium_start_system.py)
# Requires: pyrogram client instance `app` in DeadlineTech (from DeadlineTech import app)
# Also requires your existing config (config.OWNER_ID, config.SUPPORT_CHAT, config.SUPPORT_CHANNEL)
# This file contains:
# - private /start with animated GIF + loading messages -> then shows Start Panel
# - callback handlers for help/settings/owner/help submenus
# - owner panel basic callbacks (broadcast placeholder, restart placeholder)
# - my_chat_member handler to auto-welcome when bot is added to a group
# - typing/chat action animation + helpful comments
#
# NOTE: Adjust GIF / image URLs and texts to suit your bot.

from pyrogram import filters
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
    Message,
    ChatMemberUpdated,
)
import asyncio
import traceback
import config
from DeadlineTech import app

# -------------------------
# Buttons (Start / Private / Help / Owner / Settings)
# -------------------------
def start_panel(_):
    # _ is a dict of language strings
    return [
        [
            InlineKeyboardButton(text=_["S_B_1"], url=f"https://t.me/{app.username}?startgroup=true")
        ],
        [
            InlineKeyboardButton(text=_["S_B_2"], url=config.SUPPORT_CHAT),
            InlineKeyboardButton(text=_["S_B_8"], url=config.SUPPORT_CHANNEL),
        ],
        [
            InlineKeyboardButton(text=_["S_B_5"], callback_data="help_cmd"),
            InlineKeyboardButton(text=_["S_B_4"], callback_data="settings_cmd"),
        ],
    ]


def private_panel(_):
    return [
        [
            InlineKeyboardButton(text=_["S_B_3"], url=f"https://t.me/{app.username}?startgroup=true")
        ],
        [
            InlineKeyboardButton(text=_["S_B_4"], callback_data="settings_cmd"),
            InlineKeyboardButton(text=_["S_B_5"], callback_data="help_cmd"),
        ],
        [
            InlineKeyboardButton(text=_["S_B_10"], user_id=config.OWNER_ID)
        ],
        [
            InlineKeyboardButton(text=_["S_B_2"], url=config.SUPPORT_CHAT),
            InlineKeyboardButton(text=_["S_B_8"], url=config.SUPPORT_CHANNEL),
        ],
    ]


def help_panel():
    return [
        [InlineKeyboardButton("Music Commands", callback_data="music_help")],
        [InlineKeyboardButton("Admin Commands", callback_data="admin_help")],
        [InlineKeyboardButton("Owner Panel", callback_data="owner_panel")],
        [InlineKeyboardButton("Close", callback_data="close_panel")],
    ]


def settings_panel():
    return [
        [InlineKeyboardButton("Audio Quality", callback_data="quality_menu"),
         InlineKeyboardButton("Mode", callback_data="mode_menu")],
        [InlineKeyboardButton("Show/Hide Commands", callback_data="cmd_toggle")],
        [InlineKeyboardButton("Close", callback_data="close_panel")],
    ]


def owner_panel_buttons():
    return [
        [InlineKeyboardButton("Broadcast", callback_data="owner_broadcast"),
         InlineKeyboardButton("Logs", callback_data="owner_logs")],
        [InlineKeyboardButton("Restart Bot", callback_data="owner_restart")],
        [InlineKeyboardButton("Close", callback_data="close_panel")]
    ]


# -------------------------
# Language dictionary (simple, you can replace with your language loader)
# -------------------------
DEFAULT_LANG = {
    "S_B_1": "Add to Group",
    "S_B_2": "Support Chat",
    "S_B_3": "Add Music Bot",
    "S_B_4": "Settings",
    "S_B_5": "Help",
    "S_B_6": "Owner",
    "S_B_8": "Support Channel",
    "S_B_9": "Support Chat",
    "S_B_10": "Bot Owner",
    "S_B_11": "Close",
    "START_MSG": "👋 Hello! Add me to your group and enjoy nonstop music 🎵",
    "LOADING_1": "🌹 Welcome — Preparing your experience...",
    "LOADING_2": "✨ Initializing modules...",
    "LOADING_3": "🔧 Finalizing settings..."
}


# -------------------------
# /start handler (private)
# - Shows an animated GIF (rose), shows loading steps (typing/edit caption),
# - After animation and waits, edits message to show start panel with buttons.
# -------------------------
@app.on_message(filters.command("start") & filters.private)
async def premium_start_handler(client: app.__class__, message: Message):
    try:
        _ = DEFAULT_LANG.copy()  # replace with your loader if you have language files

        # 1) Send animated GIF (rose animation)
        # You may replace this GIF URL with your own hosted GIF/animation
        gif_url = "https://media.giphy.com/media/3oEjI6SIIHBdRxXI40/giphy.gif"
        m = await message.reply_animation(
            animation=gif_url,
            caption=_["LOADING_1"]
        )

        # 2) Typing / loading animation (simulate progress)
        await asyncio.sleep(1)
        try:
            # edit caption to step 2
            await m.edit_caption(_["LOADING_2"])
        except Exception:
            # Some clients do not allow edit_animation -> fallback to edit message text
            pass

        # show chat action "typing" for a moment
        try:
            await client.send_chat_action(message.chat.id, "typing")
        except Exception:
            pass
        await asyncio.sleep(1)

        await asyncio.sleep(0.8)
        try:
            await m.edit_caption(_["LOADING_3"])
        except Exception:
            pass

        # final wait (approx 2 seconds total from initial)
        await asyncio.sleep(0.5)

        # 3) Replace the caption with start message + buttons
        try:
            await m.edit_caption(
                caption=DEFAULT_LANG["START_MSG"],
                reply_markup=InlineKeyboardMarkup(start_panel(_))
            )
        except Exception:
            # If editing fails, just send a new message with buttons and delete the GIF
            try:
                await m.delete()
            except Exception:
                pass
            await message.reply_text(
                text=DEFAULT_LANG["START_MSG"],
                reply_markup=InlineKeyboardMarkup(start_panel(_))
            )

    except Exception:
        # always catch to avoid crashing handlers
        traceback.print_exc()


# -------------------------
# Callback query handlers for the buttons
# -------------------------
@app.on_callback_query()
async def callbacks_router(client: app.__class__, cq: CallbackQuery):
    data = cq.data or ""
    try:
        # generic close
        if data == "close_panel":
            await cq.answer("Closed ✅", show_alert=False)
            try:
                await cq.message.delete()
            except Exception:
                pass
            return

        # Help panel
        if data == "help_cmd":
            await cq.answer()
            await cq.message.edit_text(
                text=DEFAULT_LANG.get("HELP_MSG", "Help & Commands"),
                reply_markup=InlineKeyboardMarkup(help_panel())
            )
            return

        # Settings panel
        if data == "settings_cmd":
            await cq.answer()
            await cq.message.edit_text(
                text=DEFAULT_LANG.get("SETTINGS_MSG", "Settings"),
                reply_markup=InlineKeyboardMarkup(settings_panel())
            )
            return

        # Help submenus
        if data == "music_help":
            await cq.answer()
            await cq.message.edit_text(
                text="🎵 Music Commands:\n/play\n/pause\n/skip\n/stop\n/playlist",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="help_cmd")]])
            )
            return

        if data == "admin_help":
            await cq.answer()
            await cq.message.edit_text(
                text="🔒 Admin Commands:\n/ban\n/unban\n/mute\n/unmute",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="help_cmd")]])
            )
            return

        # Owner panel
        if data == "owner_panel":
            # only allow actual owner to use owner panel
            user_id = cq.from_user.id
            if user_id != int(config.OWNER_ID):
                await cq.answer("Only bot owner can use this.", show_alert=True)
                return
            await cq.answer()
            await cq.message.edit_text(
                text=DEFAULT_LANG.get("OWNER_PANEL", "Owner Panel"),
                reply_markup=InlineKeyboardMarkup(owner_panel_buttons())
            )
            return

        # Owner actions
        if data == "owner_broadcast":
            if cq.from_user.id != int(config.OWNER_ID):
                await cq.answer("Only owner.", show_alert=True)
                return
            await cq.answer("Send the broadcast message in private chat to the owner. (Not implemented here)", show_alert=True)
            return

        if data == "owner_restart":
            if cq.from_user.id != int(config.OWNER_ID):
                await cq.answer("Only owner.", show_alert=True)
                return
            await cq.answer("Restarting...", show_alert=False)
            # NOTE: Implement your actual restart logic here (systemctl, heroku restart, etc.)
            return

        if data == "owner_logs":
            if cq.from_user.id != int(config.OWNER_ID):
                await cq.answer("Only owner.", show_alert=True)
                return
            await cq.answer("Logs feature not implemented in handler. Check server logs.", show_alert=True)
            return

        # Quality/Mode toggles (placeholders)
        if data.startswith("quality_menu") or data.startswith("mode_menu") or data.startswith("cmd_toggle"):
            await cq.answer("Setting toggled (placeholder).", show_alert=False)
            return

        # Fallback
        await cq.answer()
    except Exception:
        traceback.print_exc()
        try:
            await cq.answer("An error occurred.", show_alert=True)
        except Exception:
            pass


# -------------------------
# When bot is added to a group: send a welcome + small start panel for group admins
# This handler uses on_my_chat_member to detect the bot being added.
# -------------------------
@app.on_my_chat_member()
async def welcome_on_added(client: app.__class__, my_chat_member: ChatMemberUpdated):
    try:
        # We care only when bot becomes a member / administrator (new status is "member" or "administrator")
        old = my_chat_member.old_chat_member
        new = my_chat_member.new_chat_member
        chat = my_chat_member.chat

        # If the bot was invited/added (old was 'left' or 'kicked' and new is 'member'/'administrator')
        old_status = getattr(old, "status", None)
        new_status = getattr(new, "status", None)

        joined_statuses = ("member", "administrator")
        left_statuses = ("left", "kicked", "banned", "none")

        if old_status in left_statuses and new_status in joined_statuses:
            # send a welcome message to group with a short intro and buttons
            try:
                text = (
                    "👋 Hello! Thanks for adding me.\n"
                    "I can play music in this group. Use /help to see commands.\n"
                    "Admins: give me necessary admin rights for best experience."
                )
                # small delay to ensure bot is fully added
                await asyncio.sleep(1.2)

                await client.send_message(
                    chat.id,
                    text,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("Add to a Group", url=f"https://t.me/{app.username}?startgroup=true")],
                        [InlineKeyboardButton("Support Chat", url=config.SUPPORT_CHAT),
                         InlineKeyboardButton("Support Channel", url=config.SUPPORT_CHANNEL)]
                    ])
                )
            except Exception:
                traceback.print_exc()
    except Exception:
        traceback.print_exc()


# -------------------------
# Optional: handler for /help in groups and private to show help panel quickly
# -------------------------
@app.on_message(filters.command("help"))
async def quick_help(client: app.__class__, message: Message):
    try:
        await message.reply_text(
            text=DEFAULT_LANG.get("HELP_MSG", "Help & Commands"),
            reply_markup=InlineKeyboardMarkup(help_panel())
        )
    except Exception:
        traceback.print_exc()
