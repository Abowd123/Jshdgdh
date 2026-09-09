import os
import zipfile
from datetime import datetime

import aiosqlite

from config import DATABASE_PATH


async def create_backup(backup_dir: str = "backups") -> str:
    """إنشاء نسخة احتياطية (ملف .zip) من قاعدة البيانات وجداولها كـ CSV."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(backup_dir, exist_ok=True)
    backup_path = f"{backup_dir}/backup_{timestamp}.zip"

    with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        if os.path.exists(DATABASE_PATH):
            zipf.write(DATABASE_PATH, os.path.basename(DATABASE_PATH))

        async with aiosqlite.connect(DATABASE_PATH) as db:
            tables = ["series", "episodes", "users", "ratings", "watch_history", "favorites"]
            for table in tables:
                try:
                    cursor = await db.execute(f"SELECT * FROM {table}")
                    rows = await cursor.fetchall()
                    columns = [d[0] for d in cursor.description]

                    csv_content = ",".join(columns) + "\n"
                    for row in rows:
                        csv_content += ",".join(
                            "" if v is None else str(v).replace(",", " ") for v in row
                        ) + "\n"

                    zipf.writestr(f"{table}.csv", csv_content)
                except Exception:
                    continue

    return backup_path


def cleanup_old_backups(backup_dir: str = "backups", keep: int = 7):
    """الاحتفاظ بآخر N نسخة احتياطية فقط وحذف الباقي."""
    if not os.path.isdir(backup_dir):
        return
    backups = sorted(
        [f for f in os.listdir(backup_dir) if f.endswith(".zip")],
        reverse=True,
    )
    for old_backup in backups[keep:]:
        try:
            os.remove(os.path.join(backup_dir, old_backup))
        except OSError:
            pass
