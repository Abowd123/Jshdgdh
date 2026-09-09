from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
import aiosqlite

from keyboards.admin_panel import AdminPanel
from config import DATABASE_PATH

router = Router()


async def get_comprehensive_stats() -> dict:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        stats = {}

        cursor = await db.execute("SELECT COUNT(*) FROM users")
        stats["total_users"] = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1")
        stats["banned_users"] = (await cursor.fetchone())[0]

        today = datetime.now().strftime("%Y-%m-%d")
        cursor = await db.execute(
            "SELECT COUNT(*) FROM users WHERE date(joined_at) = ?", (today,)
        )
        stats["new_today"] = (await cursor.fetchone())[0]

        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        cursor = await db.execute(
            "SELECT COUNT(DISTINCT user_id) FROM watch_history WHERE watched_at > ?",
            (yesterday,),
        )
        stats["active_24h"] = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COUNT(*) FROM series")
        stats["total_series"] = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COUNT(*) FROM series WHERE is_complete = 1")
        stats["complete_series"] = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COUNT(*) FROM episodes")
        stats["total_episodes"] = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT SUM(views) FROM episodes")
        stats["total_views"] = (await cursor.fetchone())[0] or 0

        cursor = await db.execute(
            "SELECT COUNT(*) FROM watch_history WHERE date(watched_at) = ?", (today,)
        )
        stats["views_today"] = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT SUM(file_size) FROM episodes")
        total_size_bytes = (await cursor.fetchone())[0] or 0
        if total_size_bytes > 1024**3:
            stats["storage"] = f"{total_size_bytes / 1024**3:.1f} GB"
        elif total_size_bytes > 1024**2:
            stats["storage"] = f"{total_size_bytes / 1024**2:.1f} MB"
        else:
            stats["storage"] = f"{total_size_bytes / 1024:.1f} KB"

        cursor = await db.execute(
            """
            SELECT s.title, SUM(e.views) as total_views
            FROM series s JOIN episodes e ON s.id = e.series_id
            GROUP BY s.id ORDER BY total_views DESC LIMIT 5
            """
        )
        stats["top_series"] = await cursor.fetchall()

        cursor = await db.execute(
            "SELECT AVG(rating), COUNT(*) FROM ratings"
        )
        avg_rating, total_ratings = await cursor.fetchone()
        stats["avg_rating"] = avg_rating or 0
        stats["total_ratings"] = total_ratings or 0

        return stats


@router.callback_query(F.data == "admin:full_stats")
async def show_full_stats(callback: CallbackQuery):
    stats = await get_comprehensive_stats()

    text = "📊 <b>الإحصائيات الشاملة</b>\n\n"
    text += "<b>👥 المستخدمين:</b>\n"
    text += f"• الإجمالي: {stats['total_users']}\n"
    text += f"• المحظورين: {stats['banned_users']}\n"
    text += f"• الجدد اليوم: {stats['new_today']}\n"
    text += f"• النشطين (24h): {stats['active_24h']}\n\n"

    text += "<b>📚 المحتوى:</b>\n"
    text += f"• المسلسلات: {stats['total_series']}\n"
    text += f"• المكتملة: {stats['complete_series']}\n"
    text += f"• الحلقات: {stats['total_episodes']}\n"
    text += f"• المساحة: {stats['storage']}\n\n"

    text += "<b>👁 المشاهدات:</b>\n"
    text += f"• الإجمالي: {stats['total_views']}\n"
    text += f"• اليوم: {stats['views_today']}\n\n"

    text += "<b>⭐ التقييمات:</b>\n"
    text += f"• المتوسط: {stats['avg_rating']:.1f}/5\n"
    text += f"• عدد المقيمين: {stats['total_ratings']}\n\n"

    if stats["top_series"]:
        text += "<b>🏆 الأكثر مشاهدة:</b>\n"
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        for i, (title, views) in enumerate(stats["top_series"]):
            text += f"{medals[i]} {title}: {views} مشاهدة\n"

    stats_kb = {
        "total_users": stats["total_users"],
        "active_today": stats["active_24h"],
        "total_series": stats["total_series"],
        "total_episodes": stats["total_episodes"],
        "total_views": stats["total_views"],
        "storage_used": stats["storage"],
    }

    await callback.message.edit_text(
        text,
        reply_markup=AdminPanel.stats_dashboard(stats_kb),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "admin:refresh_stats")
async def refresh_stats(callback: CallbackQuery):
    await show_full_stats(callback)


@router.callback_query(F.data == "admin:user_details")
async def show_user_details(callback: CallbackQuery):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("SELECT lang, COUNT(*) FROM users GROUP BY lang")
        lang_dist = await cursor.fetchall()

        cursor = await db.execute(
            """
            SELECT u.user_id, u.first_name, u.username, COUNT(wh.episode_id) as watch_count
            FROM users u JOIN watch_history wh ON u.user_id = wh.user_id
            GROUP BY u.user_id ORDER BY watch_count DESC LIMIT 10
            """
        )
        top_users = await cursor.fetchall()

    text = "👥 <b>تفاصيل المستخدمين</b>\n\n"

    if lang_dist:
        text += "<b>🌐 توزيع اللغات:</b>\n"
        for lang, count in lang_dist:
            lang_name = {"ar": "العربية", "en": "الإنجليزية"}.get(lang, lang)
            text += f"• {lang_name}: {count}\n"
        text += "\n"

    if top_users:
        text += "<b>🏆 الأكثر نشاطاً:</b>\n"
        for i, (uid, name, username, count) in enumerate(top_users, 1):
            display_name = name or username or str(uid)
            text += f"{i}. {display_name}: {count} حلقة\n"

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔙 للإحصائيات", callback_data="admin:full_stats"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin:export_stats")
async def export_stats(callback: CallbackQuery):
    stats = await get_comprehensive_stats()

    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["المؤشر", "القيمة"])
    writer.writerow(["إجمالي المستخدمين", stats["total_users"]])
    writer.writerow(["المحظورين", stats["banned_users"]])
    writer.writerow(["الجدد اليوم", stats["new_today"]])
    writer.writerow(["النشطين (24h)", stats["active_24h"]])
    writer.writerow(["المسلسلات", stats["total_series"]])
    writer.writerow(["المكتملة", stats["complete_series"]])
    writer.writerow(["الحلقات", stats["total_episodes"]])
    writer.writerow(["المشاهدات", stats["total_views"]])
    writer.writerow(["مشاهدات اليوم", stats["views_today"]])
    writer.writerow(["متوسط التقييم", f"{stats['avg_rating']:.1f}"])
    writer.writerow(["المساحة", stats["storage"]])

    csv_bytes = output.getvalue().encode("utf-8-sig")
    document = BufferedInputFile(
        csv_bytes, filename=f"stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )

    await callback.message.answer_document(document=document, caption="📊 تقرير الإحصائيات")
    await callback.answer("✅ تم تصدير الإحصائيات")
