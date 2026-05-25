#!/usr/bin/env python3
"""
🎉 Giveaway Bot
Kanal postidagi izohchilar orasidan tasodifiy g'oliblarni aniqlaydi.
Поддерживает: O'zbek | Русский | English
"""

import logging
import os
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes, ConversationHandler,
)
from pyrogram import Client as PyroClient

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── Conversation states ───────────────────────────────────────────────────────
SELECTING_LANG, WAITING_POST, WAITING_COUNT = range(3)

# ── Pyrogram client (initialized in main) ────────────────────────────────────
pyro: PyroClient = None

# ── Translations ──────────────────────────────────────────────────────────────
TEXTS = {
    "uz": {
        "welcome":    "👋 Salom! Men <b>Tanlov Botiman</b> 🎉\n\nKanal postidagi izohchilar orasidan tasodifiy g'oliblarni aniqlayman.\n\n📌 <b>Buyruqlar:</b>\n/start — Botni ishga tushirish\n/language — Tilni o'zgartirish\n/help — Yordam\n\nQuyidan tilni tanlang:",
        "lang_set":   "✅ O'zbek tili tanlandi!\n\n",
        "send_post":  "📨 Kanaldan postni menga <b>forward</b> qiling:",
        "send_count": "🔢 Nechta g'olib tanlash kerak?\n\nRaqam kiriting (masalan: <code>3</code>):",
        "bad_number": "❌ Iltimos, musbat raqam kiriting!",
        "processing": "⏳ Izohlar yuklanmoqda...",
        "no_comments":"😕 Bu post uchun izohlar topilmadi.\n\n⚠️ Botni kanalning muhokama guruhiga <b>admin</b> sifatida qo'shing.",
        "not_enough": "⚠️ Izohchilar (<b>{total}</b> ta) so'ralgan sondan (<b>{need}</b> ta) kam!\nBarchasi g'olib deb belgilandi:",
        "fwd_only":   "❌ Iltimos, kanal postini <b>forward</b> qiling!",
        "not_ch":     "❌ Bu kanal posti emas. Kanaldan post forward qiling.",
        "error":      "❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.",
        "btn_new":    "🔄 Yangi tanlov",
        "btn_lang":   "🌐 Til",
        "res_title":  "🏆 <b>G'OLIBLAR RO'YXATI</b>",
        "res_total":  "💬 Jami izohchilar",
        "res_pick":   "🎲 Tanlangan",
        "help":       "ℹ️ <b>Botdan foydalanish:</b>\n\n1️⃣ Kanaldan postni botga forward qiling\n2️⃣ G'oliblar sonini kiriting\n3️⃣ Bot tasodifiy g'oliblarni aniqlaydi\n\n⚠️ Bot kanalning <b>muhokama guruhiga admin</b> bo'lishi shart!",
    },
    "ru": {
        "welcome":    "👋 Привет! Я <b>Бот для розыгрышей</b> 🎉\n\nОпределяю случайных победителей среди комментаторов поста канала.\n\n📌 <b>Команды:</b>\n/start — Запустить бота\n/language — Сменить язык\n/help — Помощь\n\nВыберите язык ниже:",
        "lang_set":   "✅ Выбран русский язык!\n\n",
        "send_post":  "📨 Перешлите мне пост из канала:",
        "send_count": "🔢 Сколько победителей выбрать?\n\nВведите число (например: <code>3</code>):",
        "bad_number": "❌ Пожалуйста, введите корректное положительное число!",
        "processing": "⏳ Загружаю комментарии...",
        "no_comments":"😕 Комментарии не найдены.\n\n⚠️ Добавьте бота как <b>администратора</b> в группу обсуждений канала.",
        "not_enough": "⚠️ Комментаторов (<b>{total}</b>) меньше запрошенного (<b>{need}</b>)!\nВсе объявлены победителями:",
        "fwd_only":   "❌ Пожалуйста, перешлите пост из канала!",
        "not_ch":     "❌ Это не пост канала. Перешлите пост из канала.",
        "error":      "❌ Произошла ошибка. Попробуйте снова.",
        "btn_new":    "🔄 Новый розыгрыш",
        "btn_lang":   "🌐 Язык",
        "res_title":  "🏆 <b>СПИСОК ПОБЕДИТЕЛЕЙ</b>",
        "res_total":  "💬 Всего комментаторов",
        "res_pick":   "🎲 Выбрано",
        "help":       "ℹ️ <b>Как пользоваться:</b>\n\n1️⃣ Перешлите пост из канала боту\n2️⃣ Введите количество победителей\n3️⃣ Бот случайно выберет победителей\n\n⚠️ Бот должен быть <b>администратором</b> группы обсуждений!",
    },
    "en": {
        "welcome":    "👋 Hello! I'm a <b>Giveaway Bot</b> 🎉\n\nI randomly pick winners from commenters on a channel post.\n\n📌 <b>Commands:</b>\n/start — Start the bot\n/language — Change language\n/help — Help\n\nSelect your language below:",
        "lang_set":   "✅ English language selected!\n\n",
        "send_post":  "📨 Forward a channel post to me:",
        "send_count": "🔢 How many winners to select?\n\nEnter a number (e.g. <code>3</code>):",
        "bad_number": "❌ Please enter a valid positive number!",
        "processing": "⏳ Loading comments...",
        "no_comments":"😕 No comments found.\n\n⚠️ Add the bot as an <b>admin</b> to the channel's discussion group.",
        "not_enough": "⚠️ Commenters (<b>{total}</b>) are fewer than requested (<b>{need}</b>)!\nAll declared as winners:",
        "fwd_only":   "❌ Please forward a channel post!",
        "not_ch":     "❌ Not a channel post. Forward a post from a channel.",
        "error":      "❌ An error occurred. Please try again.",
        "btn_new":    "🔄 New draw",
        "btn_lang":   "🌐 Language",
        "res_title":  "🏆 <b>WINNERS LIST</b>",
        "res_total":  "💬 Total commenters",
        "res_pick":   "🎲 Selected",
        "help":       "ℹ️ <b>How to use:</b>\n\n1️⃣ Forward a channel post to the bot\n2️⃣ Enter the number of winners\n3️⃣ Bot randomly selects winners\n\n⚠️ The bot must be an <b>admin</b> of the channel's discussion group!",
    },
}

def tx(lang: str, key: str, **kw) -> str:
    text = TEXTS.get(lang, TEXTS["en"]).get(key, f"[{key}]")
    return text.format(**kw) if kw else text

def get_lang(ctx: ContextTypes.DEFAULT_TYPE) -> str:
    return ctx.user_data.get("lang", "uz")

def lang_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🇺🇿 O'zbek", callback_data="lang_uz"),
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
    ]])

def action_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(tx(lang, "btn_new"),  callback_data="new_draw"),
        InlineKeyboardButton(tx(lang, "btn_lang"), callback_data="show_lang"),
    ]])

# ── Fetch comments via Pyrogram ───────────────────────────────────────────────
async def fetch_comments(ch_id: int, msg_id: int) -> tuple[set, str | None]:
    """Returns (commenters_set, error_message_or_None)."""
    commenters = set()
    try:
        async for message in pyro.get_discussion_replies(ch_id, msg_id):
            user = message.from_user
            if not user or user.is_bot:
                continue
            if user.username:
                commenters.add(f"@{user.username}")
            else:
                name = user.first_name or ""
                if user.last_name:
                    name += f" {user.last_name}"
                if name.strip():
                    commenters.add(name.strip())
        return commenters, None
    except Exception as e:
        logger.error(f"fetch_comments error: {e}")
        return commenters, str(e)

# ── /start ────────────────────────────────────────────────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html(tx("uz", "welcome"), reply_markup=lang_kb())
    return SELECTING_LANG

# ── /help ─────────────────────────────────────────────────────────────────────
async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html(tx(get_lang(ctx), "help"))

# ── /language ─────────────────────────────────────────────────────────────────
async def cmd_language(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌐 Tilni tanlang / Выберите язык / Select language:",
        reply_markup=lang_kb()
    )
    return SELECTING_LANG

# ── Language selection callback ───────────────────────────────────────────────
async def cb_lang(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    lang = {"lang_uz": "uz", "lang_ru": "ru", "lang_en": "en"}.get(q.data, "uz")
    ctx.user_data["lang"] = lang
    await q.edit_message_text(
        tx(lang, "lang_set") + tx(lang, "send_post"),
        parse_mode="HTML"
    )
    return WAITING_POST

# ── Receive forwarded post ────────────────────────────────────────────────────
async def handle_post(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(ctx)
    msg  = update.message

    if not msg.forward_origin:
        await msg.reply_html(tx(lang, "fwd_only"))
        return WAITING_POST

    origin = msg.forward_origin
    if origin.type != "channel":
        await msg.reply_html(tx(lang, "not_ch"))
        return WAITING_POST

    ctx.user_data["ch_id"]    = origin.chat.id
    ctx.user_data["msg_id"]   = origin.message_id
    ctx.user_data["ch_title"] = origin.chat.title or "Channel"

    await msg.reply_html(tx(lang, "send_count"))
    return WAITING_COUNT

# ── Receive winner count & show results ──────────────────────────────────────
async def handle_count(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(ctx)

    try:
        need = int(update.message.text.strip())
        if need <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_html(tx(lang, "bad_number"))
        return WAITING_COUNT

    wait = await update.message.reply_text(tx(lang, "processing"))

    ch_id    = ctx.user_data.get("ch_id")
    msg_id   = ctx.user_data.get("msg_id")
    ch_title = ctx.user_data.get("ch_title", "Channel")

    try:
        pool_set, err = await fetch_comments(ch_id, msg_id)
        pool = list(pool_set)
        await wait.delete()

        if err and not pool:
            await update.message.reply_html(
                f"❌ Pyrogram xatolik:\n<code>{err}</code>\n\nch_id: <code>{ch_id}</code>  msg_id: <code>{msg_id}</code>"
            )
            return WAITING_POST

        if not pool:
            await update.message.reply_html(
                tx(lang, "no_comments"), reply_markup=action_kb(lang)
            )
            return WAITING_POST

        total  = len(pool)
        pick_n = need
        warning = ""

        if total < need:
            pick_n  = total
            warning = tx(lang, "not_enough", total=total, need=need) + "\n\n"

        winners = random.sample(pool, pick_n)

        lines = [
            tx(lang, "res_title"),
            f"📢 {ch_title}",
            "─" * 30,
            f'{tx(lang, "res_total")}: <b>{total}</b>',
            f'{tx(lang, "res_pick")}: <b>{pick_n}</b>',
            "─" * 30,
        ]
        if warning:
            lines.append(f"⚠️ {warning}")
        lines += [f"{i}. {u}" for i, u in enumerate(winners, 1)]

        await update.message.reply_html(
            "\n".join(lines), reply_markup=action_kb(lang)
        )

    except Exception as e:
        logger.error(f"handle_count error: {e}")
        try:
            await wait.delete()
        except Exception:
            pass
        await update.message.reply_html(tx(lang, "error"))

    return WAITING_POST

# ── Inline button callbacks ───────────────────────────────────────────────────
async def cb_action(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q    = update.callback_query
    lang = get_lang(ctx)
    await q.answer()

    if q.data == "new_draw":
        await q.edit_message_reply_markup(reply_markup=None)
        await ctx.bot.send_message(
            q.message.chat_id, tx(lang, "send_post"), parse_mode="HTML"
        )
        return WAITING_POST

    if q.data == "show_lang":
        await q.edit_message_reply_markup(reply_markup=None)
        await ctx.bot.send_message(
            q.message.chat_id,
            "🌐 Tilni tanlang / Выберите язык / Select language:",
            reply_markup=lang_kb()
        )
        return SELECTING_LANG

# ── App entry point ───────────────────────────────────────────────────────────
def main() -> None:
    global pyro

    TOKEN    = os.environ["BOT_TOKEN"]
    API_ID   = int(os.environ["API_ID"])
    API_HASH = os.environ["API_HASH"]

    pyro = PyroClient(
        "bot_session",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=TOKEN,
    )

    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start",    cmd_start),
            CommandHandler("language", cmd_language),
            CommandHandler("til",      cmd_language),
        ],
        states={
            SELECTING_LANG: [
                CallbackQueryHandler(cb_lang, pattern="^lang_"),
            ],
            WAITING_POST: [
                MessageHandler(
                    filters.FORWARDED & filters.ChatType.PRIVATE,
                    handle_post
                ),
                CallbackQueryHandler(cb_action, pattern="^(new_draw|show_lang)$"),
                CommandHandler("language", cmd_language),
                CommandHandler("til",      cmd_language),
            ],
            WAITING_COUNT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
                    handle_count
                ),
                CommandHandler("language", cmd_language),
            ],
        },
        fallbacks=[CommandHandler("start", cmd_start)],
        per_user=True,
        per_chat=True,
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("help", cmd_help))

    async def on_startup(_):
        await pyro.start()
        logger.info("Pyrogram started")

    async def on_shutdown(_):
        await pyro.stop()
        logger.info("Pyrogram stopped")

    app.post_init    = on_startup
    app.post_shutdown = on_shutdown

    logger.info("Bot ishga tushdi")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
