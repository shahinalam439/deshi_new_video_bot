import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from jose import jwt
from datetime import datetime, timedelta
import config
import database as db
from admin import admin_router

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()
dp.include_router(admin_router)

def make_token(uid, fid, eid):
    return jwt.encode(
        {"user_id": uid, "file_id": fid, "episode_id": eid,
         "exp": datetime.utcnow() + timedelta(hours=24)},
        config.JWT_SECRET, algorithm="HS256")

@dp.message(Command("start"))
async def start(m: types.Message):
    await db.save_user(m.from_user.id, m.from_user.username, m.from_user.first_name)
    text = (
        "🎬 **এখানে দেশি নতুন সব ভিডিও**\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🙏 **স্বাগতম, {m.from_user.first_name}!**\n\n"
        "📺 দেশি নতুন সব ওয়েব সিরিজ, নাটক ও ভিডিও\n"
        "এক জায়গায় পাবেন এখানে।\n\n"
        "✅ প্রতিদিন নতুন কনটেন্ট\n✅ HD কোয়ালিটি\n✅ সম্পূর্ণ ফ্রি\n\n"
        "👇 নিচের বাটনে ক্লিক করুন")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 সব সিরিজ দেখুন", callback_data="browse")],
        [InlineKeyboardButton(text="🔥 নতুন যোগ হয়েছে", callback_data="new")],
        [InlineKeyboardButton(text="🆘 সাহায্য", callback_data="help")]])
    await m.answer(text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(lambda c: c.data == "browse")
async def browse(cb: types.CallbackQuery):
    lst = await db.list_all_series(50)
    if not lst:
        await cb.answer("😕 এখনো কোনো সিরিজ নেই।", show_alert=True); return
    text = (f"🎬 **এখানে দেশি নতুন সব ভিডিও**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📚 **সব সিরিজ** ({len(lst)}টি):\n\nনিচ থেকে বেছে নিন 👇")
    kb = [[InlineKeyboardButton(text=f"📺 {s['title']} ({s.get('year','?')})",
                                callback_data=f"v:{s['_id']}")] for s in lst]
    kb.append([InlineKeyboardButton(text="🏠 হোম", callback_data="home")])
    await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
                               parse_mode="Markdown")
    await cb.answer()

@dp.callback_query(lambda c: c.data == "new")
async def new_releases(cb: types.CallbackQuery):
    lst = await db.list_all_series(10)
    if not lst:
        await cb.answer("😕 এখনো কিছু নেই।", show_alert=True); return
    text = ("🔥 **নতুন যোগ হয়েছে**\n━━━━━━━━━━━━━━━━━━━━\n\nসদ্য যোগ করা সিরিজ 👇")
    kb = [[InlineKeyboardButton(text=f"🆕 {s['title']} ({s.get('year','?')})",
                                callback_data=f"v:{s['_id']}")] for s in lst]
    kb.append([InlineKeyboardButton(text="🏠 হোম", callback_data="home")])
    await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
                               parse_mode="Markdown")
    await cb.answer()

@dp.callback_query(lambda c: c.data == "home")
async def home(cb: types.CallbackQuery):
    text = ("🎬 **এখানে দেশি নতুন সব ভিডিও**\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "🙏 **স্বাগতম!**\n\n"
            "📺 দেশি নতুন সব ওয়েব সিরিজ, নাটক ও ভিডিও\n"
            "এক জায়গায় পাবেন এখানে।\n\n👇 নিচের বাটনে ক্লিক করুন")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 সব সিরিজ দেখুন", callback_data="browse")],
        [InlineKeyboardButton(text="🔥 নতুন যোগ হয়েছে", callback_data="new")],
        [InlineKeyboardButton(text="🆘 সাহায্য", callback_data="help")]])
    await cb.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await cb.answer()

@dp.callback_query(lambda c: c.data == "help")
async def help_cb(cb: types.CallbackQuery):
    text = ("🆘 **সাহায্য**\n━━━━━━━━━━━━━━━━━━━━\n\n"
            "**কীভাবে ব্যবহার করবেন:**\n\n"
            "1️⃣ `/start` — মেইন মেনু\n"
            "2️⃣ 🎬 সব সিরিজ দেখুন — সব সিরিজ\n"
            "3️⃣ 🔥 নতুন যোগ হয়েছে — নতুন সিরিজ\n"
            "4️⃣ `/search <নাম>` — সিরিজ খুঁজুন\n"
            "5️⃣ সিরিজে ক্লিক → এপিসোড সিলেক্ট\n"
            "6️⃣ ১৫ সেকেন্ড বিজ্ঞাপন → ভিডিও প্লে")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 হোম", callback_data="home")]])
    await cb.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await cb.answer()

@dp.callback_query(lambda c: c.data.startswith("v:"))
async def view_series(cb: types.CallbackQuery):
    sid = cb.data.split(":", 1)[1]
    s = await db.get_series_by_id(sid)
    if not s:
        await cb.answer("😕 পাওয়া যায়নি।", show_alert=True); return
    eps = await db.get_episodes(sid)
    if not eps:
        await cb.answer("⚠️ এপিসোড নেই।", show_alert=True); return
    text = (f"📺 **{s['title']}**\n━━━━━━━━━━━━━━━━━━━━\n"
            f"📅 বছর: {s.get('year', '?')}\n"
            f"🎭 জেনার: {', '.join(s.get('genres', []))}\n"
            f"🎬 এপিসোড: {len(eps)}\n\n"
            f"📖 {s.get('description', '')[:200]}\n\n👇 এপিসোড বেছে নিন")
    kb = []
    for ep in eps:
        token = make_token(cb.from_user.id, ep["file_id"], str(ep["_id"]))
        url = f"{config.STREAM_BASE_URL}/watch/{token}"
        kb.append([InlineKeyboardButton(
            text=f"▶️ S{ep['season']:02d}E{ep['episode_num']:02d} — {ep['title']}",
            url=url)])
    kb.append([InlineKeyboardButton(text="🔙 ফিরে যান", callback_data="browse")])
    await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
                               parse_mode="Markdown")
    await cb.answer()

@dp.message(Command("search"))
async def search(m: types.Message):
    q = m.text.replace("/search", "").strip()
    if not q:
        await m.answer("🔍 **সার্চ করুন**\n\nব্যবহার: `/search সিরিজের নাম`",
                       parse_mode="Markdown"); return
    s = await db.get_series_by_name(q)
    if not s:
        await m.answer(f"😕 **'{q}'** নামে কিছু পাওয়া যায়নি।"); return
    eps = await db.get_episodes(str(s["_id"]))
    if not eps:
        await m.answer("⚠️ এপিসোড নেই।"); return
    text = f"📺 **{s['title']}**\n📅 {s.get('year', '?')}\n\n👇 এপিসোড বেছে নিন"
    kb = []
    for ep in eps:
        token = make_token(m.from_user.id, ep["file_id"], str(ep["_id"]))
        url = f"{config.STREAM_BASE_URL}/watch/{token}"
        kb.append([InlineKeyboardButton(
            text=f"▶️ S{ep['season']:02d}E{ep['episode_num']:02d} — {ep['title']}",
            url=url)])
    await m.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
                   parse_mode="Markdown")

@dp.message(Command("help"))
async def help_cmd(m: types.Message):
    text = ("🆘 **সাহায্য**\n━━━━━━━━━━━━━━━━━━━━\n\n"
            "🎬 **এখানে দেশি নতুন সব ভিডিও**\n\n"
            "**কমান্ড:**\n`/start` — মেইন মেনু\n"
            "`/search <নাম>` — সিরিজ খুঁজুন\n`/help` — সাহায্য")
    await m.answer(text, parse_mode="Markdown")

async def main():
    print(f"🚀 {config.BOT_NAME} চালু হচ্ছে...")
    await bot.delete_webhook(drop_pending_updates=True)
    me = await bot.get_me()
    print(f"✅ Bot: @{me.username}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
