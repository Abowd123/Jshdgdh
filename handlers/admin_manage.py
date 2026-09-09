import asyncio

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError
import aiosqlite

from keyboards.admin_panel import AdminPanel
from keyboards.confirmations import Confirmations
from database.queries import set_ban_status, all_user_ids, count_users
from config import DATABASE_PATH, ADMIN_IDS

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


class BroadcastState(StatesGroup):
    waiting_for_message = State()
    waiting_for_confirmation = State()


# ---------- لوحة التحكم ----------

@router.message(F.text == "/panel")
async def open_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ هذا الأمر للأدمن فقط.")
        return
    await message.answer(
        "⚙️ <b>لوحة تحكم الأدمن</b>",
        reply_markup=AdminPanel.main_panel(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "admin:panel")
async def show_panel(callback: CallbackQuery):
    await callback.message.edit_text(
        "⚙️ <b>لوحة تحكم الأدمن</b>",
        reply_markup=AdminPanel.main_panel(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "admin:series_manage")
async def series_manage(callback: CallbackQuery):
    await callback.message.edit_text(
        "📝 <b>إدارة المسلسلات</b>",
        reply_markup=AdminPanel.series_management(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "admin:add_ep")
async def hint_add_ep(callback: CallbackQuery):
    await callback.answer("أرسل الأمر /add في المحادثة", show_alert=True)


@router.callback_query(F.data == "admin:batch_add")
async def hint_batch_add(callback: CallbackQuery):
    await callback.answer(
        "أرسل: /batch اسم_المسلسل رقم_الموسم", show_alert=True
    )


@router.callback_query(F.data == "admin:new_series_hint")
async def hint_new_series(callback: CallbackQuery):
    await callback.answer("أرسل الأمر /newseries في المحادثة", show_alert=True)


@router.callback_query(F.data == "admin:del_series_hint")
async def hint_del_series(callback: CallbackQuery):
    await callback.answer("أرسل: /delseries اسم_المسلسل", show_alert=True)


@router.callback_query(F.data == "admin:del_ep_hint")
async def hint_del_ep(callback: CallbackQuery):
    await callback.answer("أرسل: /del رقم_معرف_الحلقة", show_alert=True)


@router.callback_query(F.data == "broadcast:hint")
async def hint_broadcast(callback: CallbackQuery):
    await callback.answer("أرسل الأمر /broadcast في المحادثة لبدء الإرسال الجماعي", show_alert=True)


# ---------- حذف مسلسل / حلقة ----------

@router.message(F.text.startswith("/delseries"))
async def del_series_cmd(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ هذا الأمر للأدمن فقط.")
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("❌ الاستخدام: /delseries اسم_المسلسل")
        return

    name = parts[1].strip()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "SELECT id, title FROM series WHERE title LIKE ?", (f"%{name}%",)
        )
        series = await cursor.fetchone()

    if not series:
        await message.answer(f"❌ المسلسل '{name}' غير موجود")
        return

    sid, title = series
    await message.answer(
        f"⚠️ هل تريد حذف المسلسل <b>{title}</b> وكل حلقاته؟",
        reply_markup=Confirmations.delete_confirmation("series", title, sid),
        parse_mode="HTML",
    )


@router.message(F.text.startswith("/del "))
async def del_episode_cmd(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ هذا الأمر للأدمن فقط.")
        return

    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("❌ الاستخدام: /del رقم_معرف_الحلقة")
        return

    ep_id = int(parts[1])
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            """
            SELECT e.id, s.title, e.season, e.ep_number
            FROM episodes e JOIN series s ON e.series_id = s.id
            WHERE e.id = ?
            """,
            (ep_id,),
        )
        ep = await cursor.fetchone()

    if not ep:
        await message.answer("❌ لم يتم العثور على حلقة بهذا المعرف")
        return

    _, title, season, ep_number = ep
    label = f"{title} م{season} ح{ep_number}"
    await message.answer(
        f"⚠️ هل تريد حذف الحلقة: <b>{label}</b>؟",
        reply_markup=Confirmations.delete_confirmation("episode", label, ep_id),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("confirm_delete:"))
async def confirm_delete(callback: CallbackQuery):
    _, item_type, item_id = callback.data.split(":")
    item_id = int(item_id)

    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        if item_type == "series":
            await db.execute("DELETE FROM series WHERE id = ?", (item_id,))
            msg = "✅ تم حذف المسلسل وكل حلقاته."
        elif item_type == "episode":
            cursor = await db.execute(
                "SELECT series_id FROM episodes WHERE id = ?", (item_id,)
            )
            row = await cursor.fetchone()
            await db.execute("DELETE FROM episodes WHERE id = ?", (item_id,))
            if row:
                await db.execute(
                    """
                    UPDATE series
                    SET total_eps = (SELECT COUNT(*) FROM episodes WHERE series_id = ?)
                    WHERE id = ?
                    """,
                    (row[0], row[0]),
                )
            msg = "✅ تم حذف الحلقة."
        else:
            msg = "❌ نوع غير معروف."
        await db.commit()

    await callback.message.edit_text(msg, reply_markup=AdminPanel.main_panel())
    await callback.answer()


# ---------- المستخدمون: حظر / إلغاء حظر ----------

@router.message(F.text.startswith("/ban"))
async def ban_user(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ هذا الأمر للأدمن فقط.")
        return

    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("❌ الاستخدام: /ban معرف_المستخدم")
        return

    user_id = int(parts[1])
    await set_ban_status(user_id, True)
    await message.answer(f"🚫 تم حظر المستخدم {user_id}")


@router.message(F.text.startswith("/unban"))
async def unban_user(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ هذا الأمر للأدمن فقط.")
        return

    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("❌ الاستخدام: /unban معرف_المستخدم")
        return

    user_id = int(parts[1])
    await set_ban_status(user_id, False)
    await message.answer(f"✅ تم إلغاء حظر المستخدم {user_id}")


# ---------- البث الجماعي ----------

@router.message(F.text == "/broadcast")
async def start_broadcast(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ هذا الأمر للأدمن فقط.")
        return
    await state.set_state(BroadcastState.waiting_for_message)
    await message.answer(
        "📢 أرسل الرسالة التي تريد بثّها لكل المستخدمين، أو /cancel للإلغاء:"
    )


@router.message(BroadcastState.waiting_for_message)
async def preview_broadcast(message: Message, state: FSMContext):
    await state.update_data(broadcast_text=message.html_text)
    total = await count_users()

    await message.answer(
        f"📋 <b>معاينة الرسالة:</b>\n\n{message.html_text}",
        parse_mode="HTML",
    )
    await state.set_state(BroadcastState.waiting_for_confirmation)
    await message.answer(
        "هل تريد الإرسال؟",
        reply_markup=Confirmations.broadcast_preview(message.text, total),
    )


@router.callback_query(BroadcastState.waiting_for_confirmation, F.data == "broadcast:send")
async def send_broadcast(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    text = data.get("broadcast_text", "")

    user_ids = await all_user_ids()
    sent, failed = 0, 0

    await callback.message.edit_text(f"🚀 جاري الإرسال إلى {len(user_ids)} مستخدم...")

    for uid in user_ids:
        try:
            await callback.bot.send_message(uid, text, parse_mode="HTML")
            sent += 1
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
            try:
                await callback.bot.send_message(uid, text, parse_mode="HTML")
                sent += 1
            except Exception:
                failed += 1
        except TelegramForbiddenError:
            failed += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)

    await callback.message.answer(
        f"✅ اكتمل البث\n• نجح: {sent}\n• فشل: {failed}",
        reply_markup=AdminPanel.main_panel(),
    )
    await state.clear()
    await callback.answer()


@router.callback_query(BroadcastState.waiting_for_confirmation, F.data == "broadcast:edit")
async def edit_broadcast(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BroadcastState.waiting_for_message)
    await callback.message.edit_text("✏️ أرسل الرسالة الجديدة:")
    await callback.answer()
