from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import aiosqlite

from keyboards.admin_panel import AdminPanel
from config import DATABASE_PATH, ADMIN_IDS

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


class AddEpisode(StatesGroup):
    waiting_for_video = State()
    waiting_for_series = State()
    waiting_for_number = State()
    waiting_for_title = State()


class BatchAdd(StatesGroup):
    waiting_for_videos = State()


class NewSeries(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()


# ---------- إضافة حلقة خطوة بخطوة ----------

@router.message(F.text == "/add")
async def start_add_episode(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ هذا الأمر للأدمن فقط.")
        return

    await state.set_state(AddEpisode.waiting_for_video)
    await message.answer(
        "🎬 <b>إضافة حلقة جديدة</b>\n\n"
        "أرسل الفيديو الآن:\n"
        "• يمكنك إرسال فيديو أو ملف\n"
        "• الحجم الأقصى عبر الرفع المباشر: 50 ميجابايت "
        "(لملفات أكبر، ارفعها لحسابك ثم أعد توجيهها للبوت)\n\n"
        "للإلغاء: /cancel",
        parse_mode="HTML",
    )


@router.message(AddEpisode.waiting_for_video, F.video | F.document)
async def receive_video(message: Message, state: FSMContext):
    if message.video:
        file_id = message.video.file_id
        file_unique = message.video.file_unique_id
        duration = message.video.duration
        file_size = message.video.file_size
    else:
        file_id = message.document.file_id
        file_unique = message.document.file_unique_id
        duration = 0
        file_size = message.document.file_size

    await state.update_data(
        file_id=file_id,
        file_unique=file_unique,
        duration=duration,
        file_size=file_size,
    )

    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("SELECT id, title FROM series ORDER BY title")
        series_list = await cursor.fetchall()

    if not series_list:
        await message.answer(
            "❌ لا توجد مسلسلات بعد.\n"
            "أنشئ مسلسلاً أولاً باستخدام /newseries"
        )
        await state.clear()
        return

    builder = InlineKeyboardBuilder()
    for sid, title in series_list:
        builder.button(text=title, callback_data=f"select_series:{sid}")
    builder.button(text="➕ مسلسل جديد", callback_data="new_series")
    builder.adjust(2)

    await state.set_state(AddEpisode.waiting_for_series)
    await message.answer("📚 اختر المسلسل:", reply_markup=builder.as_markup())


@router.message(AddEpisode.waiting_for_video)
async def wrong_video_input(message: Message):
    await message.answer("⚠️ الرجاء إرسال فيديو أو ملف، أو /cancel للإلغاء.")


@router.callback_query(AddEpisode.waiting_for_series, F.data.startswith("select_series:"))
async def select_series(callback: CallbackQuery, state: FSMContext):
    series_id = int(callback.data.split(":")[1])

    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "SELECT title FROM series WHERE id = ?", (series_id,)
        )
        series = await cursor.fetchone()

        cursor = await db.execute(
            "SELECT MAX(ep_number) FROM episodes WHERE series_id = ?",
            (series_id,),
        )
        last_ep = await cursor.fetchone()

    next_ep = (last_ep[0] or 0) + 1

    await state.update_data(series_id=series_id)
    await state.set_state(AddEpisode.waiting_for_number)

    await callback.message.edit_text(
        f"🔢 <b>{series[0]}</b>\n\n"
        f"أرسل رقم الحلقة:\n"
        f"• الرقم التالي المتاح: <b>{next_ep}</b>\n"
        f"• أو أرسل 'تلقائي' لاستخدام {next_ep}\n\n"
        f"للإلغاء: /cancel",
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(AddEpisode.waiting_for_series, F.data == "new_series")
async def prompt_new_series_from_add(callback: CallbackQuery, state: FSMContext):
    await state.set_state(NewSeries.waiting_for_title)
    await callback.message.edit_text("📝 أرسل اسم المسلسل الجديد:")
    await callback.answer()


@router.message(AddEpisode.waiting_for_number)
async def receive_episode_number(message: Message, state: FSMContext):
    data = await state.get_data()
    series_id = data["series_id"]

    if message.text.strip().lower() in ("تلقائي", "auto"):
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute(
                "SELECT MAX(ep_number) FROM episodes WHERE series_id = ?",
                (series_id,),
            )
            last_ep = await cursor.fetchone()
        ep_number = (last_ep[0] or 0) + 1
    else:
        try:
            ep_number = int(message.text.strip())
        except ValueError:
            await message.answer("❌ الرجاء إرسال رقم صحيح أو كلمة 'تلقائي'")
            return

    await state.update_data(ep_number=ep_number)
    await state.set_state(AddEpisode.waiting_for_title)

    await message.answer(
        "📝 أرسل عنوان الحلقة:\n"
        "• أو أرسل /skip للتخطي\n\n"
        "للإلغاء: /cancel"
    )


@router.message(AddEpisode.waiting_for_title)
async def receive_title(message: Message, state: FSMContext):
    title = None if message.text == "/skip" else message.text

    data = await state.get_data()

    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute(
                """
                INSERT INTO episodes
                (series_id, ep_number, season, title, file_id, file_unique, duration, file_size)
                VALUES (?, ?, 1, ?, ?, ?, ?, ?)
                """,
                (
                    data["series_id"],
                    data["ep_number"],
                    title,
                    data["file_id"],
                    data["file_unique"],
                    data["duration"],
                    data["file_size"],
                ),
            )
            await db.execute(
                """
                UPDATE series
                SET total_eps = (SELECT COUNT(*) FROM episodes WHERE series_id = ?)
                WHERE id = ?
                """,
                (data["series_id"], data["series_id"]),
            )
            await db.commit()
        except aiosqlite.IntegrityError:
            await message.answer(
                "⚠️ هذه الحلقة (نفس الرقم لنفس المسلسل) مضافة مسبقاً."
            )
            await state.clear()
            return
        except Exception as e:
            await message.answer(f"❌ خطأ: {e}")
            await state.clear()
            return

        cursor = await db.execute(
            "SELECT title FROM series WHERE id = ?", (data["series_id"],)
        )
        series_title = (await cursor.fetchone())[0]

    await message.answer(
        f"✅ <b>تمت الإضافة بنجاح!</b>\n\n"
        f"📺 {series_title}\n"
        f"🎬 الموسم 1 • الحلقة {data['ep_number']}\n"
        f"{'📝 ' + title if title else ''}",
        parse_mode="HTML",
        reply_markup=AdminPanel.main_panel(),
    )

    await state.clear()


# ---------- إنشاء مسلسل جديد ----------

@router.message(F.text == "/newseries")
async def start_new_series(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ هذا الأمر للأدمن فقط.")
        return
    await state.set_state(NewSeries.waiting_for_title)
    await message.answer("📝 أرسل اسم المسلسل الجديد:")


@router.message(NewSeries.waiting_for_title)
async def new_series_title(message: Message, state: FSMContext):
    await state.update_data(new_title=message.text.strip())
    await state.set_state(NewSeries.waiting_for_description)
    await message.answer("📝 أرسل وصفاً مختصراً للمسلسل، أو /skip للتخطي:")


@router.message(NewSeries.waiting_for_description)
async def new_series_description(message: Message, state: FSMContext):
    description = None if message.text == "/skip" else message.text
    data = await state.get_data()
    title = data["new_title"]

    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute(
                "INSERT INTO series (title, description) VALUES (?, ?)",
                (title, description),
            )
            await db.commit()
        except aiosqlite.IntegrityError:
            await message.answer(f"⚠️ يوجد مسلسل بهذا الاسم مسبقاً: {title}")
            await state.clear()
            return

    await message.answer(
        f"✅ تم إنشاء المسلسل: <b>{title}</b>\n\n"
        f"يمكنك الآن إضافة حلقات له عبر /add أو /batch",
        parse_mode="HTML",
        reply_markup=AdminPanel.main_panel(),
    )
    await state.clear()


# ---------- الوضع السريع (Batch) ----------

@router.message(F.text.startswith("/batch"))
async def start_batch_add(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ هذا الأمر للأدمن فقط.")
        return

    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer(
            "❌ الاستخدام: /batch اسم_المسلسل رقم_الموسم\n"
            "مثال: /batch ناروتو 1"
        )
        return

    series_name = parts[1]
    try:
        season = int(parts[2])
    except ValueError:
        await message.answer("❌ رقم الموسم يجب أن يكون رقماً صحيحاً")
        return

    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "SELECT id, title FROM series WHERE title LIKE ?", (f"%{series_name}%",)
        )
        series = await cursor.fetchone()

    if not series:
        await message.answer(f"❌ المسلسل '{series_name}' غير موجود")
        return

    series_id, series_title = series

    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "SELECT MAX(ep_number) FROM episodes WHERE series_id = ? AND season = ?",
            (series_id, season),
        )
        last_ep = await cursor.fetchone()
    start_number = (last_ep[0] or 0) + 1

    await state.update_data(series_id=series_id, season=season, counter=start_number)
    await state.set_state(BatchAdd.waiting_for_videos)

    await message.answer(
        f"⚡ <b>الوضع السريع مفعّل</b>\n\n"
        f"📺 المسلسل: {series_title}\n"
        f"📅 الموسم: {season}\n"
        f"🔢 ستبدأ الترقيم من: {start_number}\n\n"
        f"ابدأ بإرسال الفيديوهات بالترتيب.\n"
        f"أرسل /done للإنهاء.",
        parse_mode="HTML",
    )


@router.message(BatchAdd.waiting_for_videos, F.video | F.document)
async def batch_receive_video(message: Message, state: FSMContext):
    data = await state.get_data()

    if message.video:
        file_id = message.video.file_id
        file_unique = message.video.file_unique_id
    else:
        file_id = message.document.file_id
        file_unique = message.document.file_unique_id

    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute(
                """
                INSERT INTO episodes (series_id, ep_number, season, file_id, file_unique)
                VALUES (?, ?, ?, ?, ?)
                """,
                (data["series_id"], data["counter"], data["season"], file_id, file_unique),
            )
            await db.commit()
        except aiosqlite.IntegrityError:
            await message.answer(f"⚠️ حلقة {data['counter']} موجودة مسبقاً، تم تخطيها")
            await state.update_data(counter=data["counter"] + 1)
            return

    await message.answer(f"✅ حلقة {data['counter']} ✓")
    await state.update_data(counter=data["counter"] + 1)


@router.message(BatchAdd.waiting_for_videos, F.text == "/done")
async def finish_batch(message: Message, state: FSMContext):
    data = await state.get_data()

    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """
            UPDATE series
            SET total_eps = (SELECT COUNT(*) FROM episodes WHERE series_id = ?)
            WHERE id = ?
            """,
            (data["series_id"], data["series_id"]),
        )
        await db.commit()

        cursor = await db.execute(
            "SELECT COUNT(*) FROM episodes WHERE series_id = ? AND season = ?",
            (data["series_id"], data["season"]),
        )
        total_in_season = (await cursor.fetchone())[0]

    await message.answer(
        f"🎉 <b>تم الانتهاء!</b>\n\n"
        f"إجمالي حلقات الموسم {data['season']} الآن: {total_in_season}",
        parse_mode="HTML",
        reply_markup=AdminPanel.main_panel(),
    )

    await state.clear()


@router.message(BatchAdd.waiting_for_videos)
async def batch_wrong_input(message: Message):
    await message.answer("⚠️ أرسل فيديو/ملف، أو /done لإنهاء الوضع السريع.")
