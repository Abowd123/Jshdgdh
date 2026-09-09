# بوت مسلسلات كرتون على تليجرام (نسخة مدمجة)

بوت تيليجرام لتصفح وإدارة ومشاهدة حلقات المسلسلات الكرتونية، مبني بـ `aiogram 3` و `SQLite`.
الفيديوهات لا تُخزَّن على السيرفر — يُحتفظ فقط بـ `file_id` من تيليجرام، ويُعاد إرسالها منه مباشرة.

> هذه النسخة تدمج مشروعين سابقين لنفس فكرة البوت في مشروع واحد أقوى:
> النسخة الأساسية (الأكثر اكتمالاً: تقييمات، بحث Inline، إحصائيات، نسخ احتياطي تلقائي، حماية من التكرار)
> بالإضافة إلى تحسينات من النسخة الثانية (لوحة أزرار سفلية ثابتة للوصول السريع)، مع إكمال أمر `/search` للبحث المباشر بالكتابة الذي كان ناقصاً.

## ما الجديد في النسخة المدمجة

- **لوحة أزرار سفلية ثابتة (Quick Menu)** تظهر بعد `/start`، وتختلف تلقائياً بين المستخدم العادي والأدمن، وتعمل جنباً إلى جنب مع القوائم الشفافة (Inline) الأصلية دون أن تلغيها.
- **أمر `/search` فعّال** (وزر «🔍 بحث»): يمكنك الآن كتابة اسم المسلسل مباشرة في المحادثة للبحث عنه، إضافة إلى البحث المتقدم بالفلاتر والبحث عبر وضع Inline (`@اسم_البوت`).
- توحيد كل ميزات الإدارة (إضافة سريعة، لوحة تحكم، نسخ احتياطي، إحصائيات) خلف أزرار مباشرة في لوحة الأدمن السفلية.

## 1. المتطلبات

- Python 3.11+
- توكن بوت من [@BotFather](https://t.me/BotFather)

## 2. التثبيت

```bash
python -m venv .venv
source .venv/bin/activate      # على ويندوز: .venv\Scripts\activate
pip install -r requirements.txt
```

## 3. الإعداد

انسخ `.env.example` إلى `.env` واملأ القيم:

```bash
cp .env.example .env
```

- `BOT_TOKEN`: التوكن من BotFather
- `ADMIN_IDS`: معرف تيليجرام الرقمي لكل أدمن (مفصولة بفاصلة)
- باقي القيم اختيارية (اشتراك إجباري، قناة أرشيف، نسخ احتياطي تلقائي)

## 4. التشغيل

```bash
python bot.py
```

عند أول تشغيل تُنشأ قاعدة البيانات تلقائياً في `data/bot.db`.

## 4.1 التنصيب على Railway

المشروع جاهز للنشر على [Railway](https://railway.app) — يحتوي على `Procfile` و `.python-version` يتعرف عليهما Railway تلقائياً (Nixpacks).

**الطريقة أ: عبر GitHub**

1. ارفع مجلد المشروع كـ repo على GitHub.
2. في Railway: **New Project → Deploy from GitHub repo** واختر الـ repo.
3. من تبويب **Variables** أضف المتغيرات:
   - `BOT_TOKEN`
   - `ADMIN_IDS`
   - (اختياري) `AUTO_BACKUP_HOURS`, `REQUIRE_SUBSCRIPTION`, `MAIN_CHANNEL_ID`, `ARCHIVE_CHANNEL_ID`
4. **مهم لثبات قاعدة البيانات**: نظام ملفات Railway غير دائم (يُمسح مع كل نشر جديد). أضف **Volume** من تبويب المشروع:
   - أنشئ Volume واربطه بمسار مثل `/data`
   - أضف متغيّر `DATABASE_PATH=/data/bot.db`
5. Railway سيبني وينشر المشروع تلقائياً، ويشغّل `python bot.py` كـ worker (بدون منفذ HTTP، لأن البوت يعمل بنظام Polling).
6. راقب اللوقات (Logs) للتأكد من ظهور: `✅ تم تهيئة قاعدة البيانات` و `✅ تم تحميل جميع الموجهات`.

**الطريقة ب: عبر Railway CLI مباشرة من جهازك**

```bash
npm install -g @railway/cli
railway login
cd cartoon_bot_merged
railway init
railway up
```

ثم أضف المتغيرات والـ Volume بنفس الخطوات أعلاه من لوحة تحكم Railway على الويب.

> ملاحظة: لا تحتاج فتح أي منفذ (Port) — هذا البوت لا يستقبل Webhooks، بل يسحب التحديثات بنفسه (`start_polling`)، لذلك لا تربطه بـ Public Networking في Railway.

## 5. أوامر الأدمن

| الأمر | الوصف |
|---|---|
| `/newseries` | إنشاء مسلسل جديد (خطوة بخطوة) |
| `/add` | إضافة حلقة واحدة (خطوة بخطوة) |
| `/batch اسم_المسلسل رقم_الموسم` | الوضع السريع لإضافة عدة حلقات متتالية |
| `/del رقم_معرف_الحلقة` | حذف حلقة (يطلب تأكيد) |
| `/delseries اسم_المسلسل` | حذف مسلسل كامل (يطلب تأكيد) |
| `/ban معرف_المستخدم` / `/unban معرف_المستخدم` | حظر/رفع حظر مستخدم |
| `/broadcast` | إرسال رسالة جماعية لكل المستخدمين |
| `/backup` | نسخة احتياطية فورية لقاعدة البيانات |
| `/panel` | فتح لوحة تحكم الأدمن بالأزرار |

## 6. أوامر المستخدم

`/start`, `/help`, `/search`, `/cancel` — والباقي عبر الأزرار (تصفح، مفضلة، الأكثر مشاهدة، آخر الإضافات...)
سواء من القائمة الشفافة (Inline) بعد `/start`، أو من لوحة الأزرار السفلية الثابتة.

## 7. ملاحظة حول حجم الملفات

الحد الأقصى لرفع فيديو مباشرة للبوت هو 50 ميجابايت (قيود Bot API القياسي).
للحلقات الأكبر: ارفعها من حسابك الشخصي إلى قناة (حتى 2-4 جيجا)، ثم أعد توجيهها للبوت — سيحصل البوت على `file_id` صالح للإرسال لاحقاً دون قيود الرفع.

## 8. هيكل المشروع

```
cartoon_bot/
├── bot.py
├── config.py
├── database/
│   ├── models.py
│   └── queries.py
├── handlers/
│   ├── start.py
│   ├── admin_add.py
│   ├── admin_manage.py
│   ├── admin_stats.py
│   ├── admin_backup.py
│   ├── user_browse.py
│   ├── search.py
│   ├── ratings.py
│   ├── inline.py
│   ├── menu_nav.py        # جديد: يربط الأزرار السفلية بمنطق الميزات الأصلي
│   └── fallback.py
├── keyboards/
│   ├── main_menu.py, series_browse.py, series_detail.py,
│   ├── episode_player.py, admin_panel.py, confirmations.py,
│   ├── notifications.py, advanced_search.py, rating_system.py,
│   ├── watchlist.py, inline_kb.py, pagination.py, reply_kb.py (جديد)
├── middlewares/
│   ├── admin_check.py, subscription.py, throttling.py
├── utils/
│   ├── normalize.py, backup.py
├── requirements.txt
├── Procfile               # جديد: لتشغيل البوت كـ worker على Railway
├── .python-version        # جديد: يحدد إصدار بايثون لـ Railway/Nixpacks
├── .env.example
└── data/bot.db  (يُنشأ تلقائياً)
```
