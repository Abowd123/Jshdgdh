import aiosqlite
import os
from config import DATABASE_PATH


async def init_db():
    """تهيئة قاعدة البيانات وإنشاء الجداول"""
    os.makedirs(os.path.dirname(DATABASE_PATH) or ".", exist_ok=True)

    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        await db.executescript(
            """
            CREATE TABLE IF NOT EXISTS series (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL UNIQUE,
                description TEXT,
                poster_id TEXT,
                total_eps INTEGER DEFAULT 0,
                is_complete INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS series_aliases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                series_id INTEGER NOT NULL,
                alias TEXT NOT NULL,
                FOREIGN KEY (series_id) REFERENCES series(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                series_id INTEGER NOT NULL,
                ep_number INTEGER NOT NULL,
                season INTEGER DEFAULT 1,
                title TEXT,
                file_id TEXT NOT NULL,
                file_unique TEXT,
                duration INTEGER,
                file_size INTEGER,
                views INTEGER DEFAULT 0,
                added_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (series_id) REFERENCES series(id) ON DELETE CASCADE,
                UNIQUE(series_id, season, ep_number)
            );

            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
                is_banned INTEGER DEFAULT 0,
                lang TEXT DEFAULT 'ar'
            );

            CREATE TABLE IF NOT EXISTS favorites (
                user_id INTEGER,
                series_id INTEGER,
                added_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, series_id),
                FOREIGN KEY (series_id) REFERENCES series(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS watch_history (
                user_id INTEGER,
                episode_id INTEGER,
                watched_at TEXT DEFAULT CURRENT_TIMESTAMP,
                progress REAL DEFAULT 0,
                FOREIGN KEY (episode_id) REFERENCES episodes(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS ratings (
                user_id INTEGER,
                series_id INTEGER,
                season INTEGER,
                ep_number INTEGER,
                rating INTEGER CHECK(rating BETWEEN 1 AND 5),
                review TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, series_id, season, ep_number)
            );

            CREATE INDEX IF NOT EXISTS idx_episodes_series
            ON episodes(series_id, season, ep_number);

            CREATE INDEX IF NOT EXISTS idx_watch_history_user
            ON watch_history(user_id);

            CREATE INDEX IF NOT EXISTS idx_ratings_series
            ON ratings(series_id);

            CREATE INDEX IF NOT EXISTS idx_aliases_series
            ON series_aliases(series_id);
            """
        )
        await db.commit()
