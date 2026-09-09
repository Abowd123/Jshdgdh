"""
كل استعلامات SQL المشتركة في مكان واحد لتسهيل الصيانة.
الاستعلامات الخاصة جداً بمنطق شاشة معينة تبقى داخل الهاندلر الخاص بها.
"""
import aiosqlite
from config import DATABASE_PATH


# ---------- المستخدمون ----------

async def upsert_user(user_id: int, username: str | None, first_name: str | None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """
            INSERT INTO users (user_id, username, first_name)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name
            """,
            (user_id, username, first_name),
        )
        await db.commit()


async def is_user_banned(user_id: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "SELECT is_banned FROM users WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        return bool(row and row[0])


async def set_ban_status(user_id: int, banned: bool):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE users SET is_banned = ? WHERE user_id = ?",
            (1 if banned else 0, user_id),
        )
        await db.commit()


async def count_users() -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        return (await cursor.fetchone())[0]


async def all_user_ids() -> list[int]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "SELECT user_id FROM users WHERE is_banned = 0"
        )
        rows = await cursor.fetchall()
        return [r[0] for r in rows]


# ---------- المسلسلات والحلقات ----------

async def get_series_list(order_by: str = "title") -> list[tuple]:
    allowed = {"title", "created_at", "total_eps"}
    if order_by not in allowed:
        order_by = "title"
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            f"SELECT id, title, total_eps FROM series ORDER BY {order_by}"
        )
        return await cursor.fetchall()


async def get_series_by_id(series_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "SELECT id, title, description, poster_id, total_eps, is_complete "
            "FROM series WHERE id = ?",
            (series_id,),
        )
        return await cursor.fetchone()


async def create_series(title: str, description: str | None = None) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO series (title, description) VALUES (?, ?)",
            (title, description),
        )
        await db.commit()
        return cursor.lastrowid


async def delete_series(series_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM series WHERE id = ?", (series_id,))
        await db.commit()


async def delete_episode(episode_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM episodes WHERE id = ?", (episode_id,))
        await db.commit()


async def recalc_total_eps(series_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """
            UPDATE series
            SET total_eps = (SELECT COUNT(*) FROM episodes WHERE series_id = ?)
            WHERE id = ?
            """,
            (series_id, series_id),
        )
        await db.commit()


async def next_episode_number(series_id: int, season: int = 1) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "SELECT MAX(ep_number) FROM episodes WHERE series_id = ? AND season = ?",
            (series_id, season),
        )
        row = await cursor.fetchone()
        return (row[0] or 0) + 1
