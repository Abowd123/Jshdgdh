import os
from dotenv import load_dotenv

load_dotenv()

# إعدادات البوت
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

# إعدادات القناة
ARCHIVE_CHANNEL_ID = int(os.getenv("ARCHIVE_CHANNEL_ID", "0") or 0)
MAIN_CHANNEL_ID = int(os.getenv("MAIN_CHANNEL_ID", "0") or 0)          # قناة الاشتراك الإجباري
REQUIRE_SUBSCRIPTION = os.getenv("REQUIRE_SUBSCRIPTION", "false").lower() == "true"

# إعدادات قاعدة البيانات
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/bot.db")

# إعدادات عامة
ITEMS_PER_PAGE = 20
EPISODES_PER_ROW = 5
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

# النسخ الاحتياطي التلقائي
AUTO_BACKUP_HOURS = int(os.getenv("AUTO_BACKUP_HOURS", "24"))
