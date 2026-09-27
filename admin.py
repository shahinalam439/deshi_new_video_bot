from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
import config
import database as db

admin_router = Router()

def is_admin(uid):
    return uid in config.ADMIN_IDS

class AddSeries(StatesGroup):
    title = State(); desc = State(); poster = State()
    genres = State(); year = State(); confirm = State()

class AddEpisode(StatesGroup):
    select = State(); season = State()
    epnum = State(); title = State(); video = State()

class Broadcast(StatesGroup):
    msg = State(); confirm = State()

def menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ নতুন সিরিজ"), KeyboardButton(text="🎬 এপিসোড যোগ")],
            [KeyboardButton(text="📊 স্ট্যাটস"), KeyboardButton(text="📢 ব্রডকাস্ট")],
            [KeyboardButton(text="🗑️ ডিলিট"), KeyboardButton(text="❌ বন্ধ")],
        ], resize_keyboard=True)

@admin_router.message(Command("admin"))
async def admin_start(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ আপনি অ্যাডমিন নন।")
        return
    await message.answer(
        "🛠️ **অ্যাডমিন প্যানেল**\n🎬 এখানে দেশি নতুন সব ভিডিও\n"
        "━━━━━━━━━━━━━━━━━━━━\n\nনিচের মেনু থেকে বেছে নিন:",
        reply_markup=menu())

@admin_router.message(F.text == "❌ বন্ধ")
async def admin_close(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ বন্ধ।", reply_markup=ReplyKeyboardRemove())

@admin_router.message(F.text == "➕ নতুন সিরিজ")
async def ns1(m: types.Message, state: FSMContext):
    if not is_admin(m.from_user.id): return
    await m.answer("📝 সিরিজের **নাম** লিখুন:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(AddSeries.title)

@admin_router.message(AddSeries.title)
async def ns2(m: types.Message, state: FSMContext):
    await state.update_data(title=m.text)
    await m.answer("📖 **বিবরণ** লিখুন:")
    await state.set_state(AddSeries.desc)

@admin_router.message(AddSeries.desc)
async def ns3(m: types.Message, state: FSMContext):
    await state.update_data(desc=m.text)
    await m.answer("🖼️ **পোস্টার URL** (বা 'skip'):")
    await state.set_state(AddSeries.poster)

@admin_router.message(AddSeries.poster)
async def ns4(m: types.Message, state: FSMContext):
    p = "" if m.text.lower() == "skip" else m.text
    await state.update_data(poster=p)
    await m.answer("🎭 **জেনার** (কমা দিয়ে):")
    await state.set_state(AddSeries.genres)

@admin_router.message(AddSeries.genres)
async def ns5(m: types.Message, state: FSMContext):
    await state.update_data(genres=[g.strip() for g in m.text.split(",")])
    await m.answer("📅 **বছর**:")
    await state.set_state(AddSeries.year)

@admin_router.message(AddSeries.year)
async def ns6(m: types.Message, state: FSMContext):
    await state.update_data(year=m.text)
    d = await state.get_data()
    preview = (f"✅ **নিশ্চিত করুন**\n\n📺 {d['title']}\n"
               f"📖 {d['desc'][:80]}...\n🎭 {', '.join(d['genres'])}\n📅 {d['year']}")
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ সেভ", callback_data="sv"),
        InlineKeyboardButton(text="❌ বাতিল", callback_data="cn")]])
    await m.answer(preview, reply_markup=kb)
    await state.set_state(AddSeries.confirm)

@admin_router.callback_query(F.data == "sv", AddSeries.confirm)
async def sv_series(cb: types.CallbackQuery, state: FSMContext):
    d = await state.get_data()
    sid = await db.create_series(d["title"], d["desc"], d["poster"], d["genres"], d["year"])
    await cb.message.edit_text(f"✅ সেভ হয়েছে!\n🆔 `{sid}`", parse_mode="Markdown")
    await state.clear()
    await cb.message.answer("মেনু:", reply_markup=menu())

@admin_router.callback_query(F.data == "cn")
async def cn_series(cb: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text("❌ বাতিল।")
    await cb.message.answer("মেনু:", reply_markup=menu())

@admin_router.message(F.text == "🎬 এপিসোড যোগ")
async def ae1(m: types.Message, state: FSMContext):
    if not is_admin(m.from_user.id): return
    lst = await db.list_all_series(50)
    if not lst:
        await m.answer("⚠️ আগে সিরিজ যোগ করুন।")
        return
    kb = [[InlineKeyboardButton(text=f"📺 {s['title']}",
                                callback_data=f"ep:{s['_id']}")] for s in lst]
    await m.answer("কোন সিরিজে?", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    await state.set_state(AddEpisode.select)

@admin_router.callback_query(F.data.startswith("ep:"), AddEpisode.select)
async def ae2(cb: types.CallbackQuery, state: FSMContext):
    await state.update_data(sid=cb.data.split(":")[1])
    await cb.message.edit_text("🔢 **সিজন নাম্বার**:")
    await state.set_state(AddEpisode.season)

@admin_router.message(AddEpisode.season)
async def ae3(m: types.Message, state: FSMContext):
    await state.update_data(season=int(m.text))
    await m.answer("🎯 **এপিসোড নাম্বার**:")
    await state.set_state(AddEpisode.epnum)

@admin_router.message(AddEpisode.epnum)
async def ae4(m: types.Message, state: FSMContext):
    await state.update_data(epnum=int(m.text))
    await m.answer("📝 **টাইটেল**:")
    await state.set_state(AddEpisode.title)

@admin_router.message(AddEpisode.title)
async def ae5(m: types.Message, state: FSMContext):
    await state.update_data(title=m.text)
    await m.answer("🎥 **ভিডিও ফাইল পাঠান**:")
    await state.set_state(AddEpisode.video)

@admin_router.message(AddEpisode.video, F.video | F.document)
async def ae6(m: types.Message, state: FSMContext):
    if m.video:
        fid, fuid = m.video.file_id, m.video.file_unique_id
    else:
        fid, fuid = m.document.file_id, m.document.file_unique_id
    d = await state.get_data()
    await db.add_episode(d["sid"], d["season"], d["epnum"], d["title"], fid, fuid)
    await m.answer(f"✅ সেভ!\nS{d['season']:02d}E{d['epnum']:02d} — {d['title']}",
                   reply_markup=menu())
    await state.clear()

@admin_router.message(F.text == "📊 স্ট্যাটস")
async def stats(m: types.Message):
    if not is_admin(m.from_user.id): return
    u = await db.get_total_users()
    s = await db.get_total_series()
    e = await db.get_total_episodes()
    v = await db.get_total_views()
    await m.answer(f"📊 **বট স্ট্যাটস**\n\n👥 ইউজার: `{u}`\n"
                   f"📺 সিরিজ: `{s}`\n🎬 এপিসোড: `{e}`\n👁️ ভিউ: `{v}`",
                   parse_mode="Markdown")

@admin_router.message(F.text == "📢 ব্রডকাস্ট")
async def bc1(m: types.Message, state: FSMContext):
    if not is_admin(m.from_user.id): return
    await m.answer("📢 মেসেজ লিখুন:")
    await state.set_state(Broadcast.msg)

@admin_router.message(Broadcast.msg)
async def bc2(m: types.Message, state: FSMContext):
    await state.update_data(msg=m.text)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ পাঠান", callback_data="bc_ok"),
        InlineKeyboardButton(text="❌ বাতিল", callback_data="bc_no")]])
    await m.answer(f"প্রিভিউ:\n\n{m.text}", reply_markup=kb)
    await state.set_state(Broadcast.confirm)

@admin_router.callback_query(F.data == "bc_ok", Broadcast.confirm)
async def bc3(cb: types.CallbackQuery, state: FSMContext):
    d = await state.get_data()
    ids = await db.get_all_user_ids()
    ok = fail = 0
    for uid in ids:
        try:
            await cb.bot.send_message(uid, d["msg"]); ok += 1
        except Exception:
            fail += 1
    await cb.message.edit_text(f"✅ সফল: {ok}, ব্যর্থ: {fail}")
    await state.clear()

@admin_router.callback_query(F.data == "bc_no")
async def bc4(cb: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text("❌ বাতিল।")

@admin_router.message(F.text == "🗑️ ডিলিট")
async def dl1(m: types.Message):
    if not is_admin(m.from_user.id): return
    lst = await db.list_all_series(50)
    if not lst:
        await m.answer("⚠️ কিছু নেই।"); return
    kb = [[InlineKeyboardButton(text=f"🗑️ {s['title']}",
                                callback_data=f"dl:{s['_id']}")] for s in lst]
    await m.answer("কোনটি?", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@admin_router.callback_query(F.data.startswith("dl:"))
async def dl2(cb: types.CallbackQuery):
    await db.delete_series(cb.data.split(":")[1])
    await cb.message.edit_text("✅ ডিলিট হয়েছে।")
