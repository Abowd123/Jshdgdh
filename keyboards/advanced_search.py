from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class AdvancedSearch:
    """نظام البحث المتقدم مع فلاتر"""

    @staticmethod
    def search_filters():
        builder = InlineKeyboardBuilder()

        builder.row(
            InlineKeyboardButton(text="🎭 النوع", callback_data="filter:genre"),
            InlineKeyboardButton(text="📅 السنة", callback_data="filter:year"),
        )
        builder.row(
            InlineKeyboardButton(text="✅ مكتمل", callback_data="filter:complete"),
            InlineKeyboardButton(text="🔄 مستمر", callback_data="filter:ongoing"),
        )
        builder.row(
            InlineKeyboardButton(text="⭐ الأعلى تقييماً", callback_data="filter:top_rated"),
            InlineKeyboardButton(text="👁 الأكثر مشاهدة", callback_data="filter:most_viewed"),
        )
        builder.row(
            InlineKeyboardButton(text="📺 أقل من 50 حلقة", callback_data="filter:short"),
            InlineKeyboardButton(text="📺 أكثر من 100 حلقة", callback_data="filter:long"),
        )
        builder.row(InlineKeyboardButton(text="🔄 إعادة تعيين الفلاتر", callback_data="filter:reset"))
        builder.row(
            InlineKeyboardButton(text="🔍 تطبيق الفلتر", callback_data="search:apply_filters"),
        )
        builder.row(
            InlineKeyboardButton(text="🔍 بحث بالنص", switch_inline_query_current_chat=""),
            InlineKeyboardButton(text="🔙 رجوع", callback_data="main_menu"),
        )

        return builder.as_markup()

    @staticmethod
    def genre_selection(genres: list, selected: set | None = None):
        if selected is None:
            selected = set()

        builder = InlineKeyboardBuilder()
        genre_emojis = {
            "أكشن": "⚔️", "مغامرات": "🗺", "كوميدي": "😂", "دراما": "🎭",
            "خيال علمي": "🚀", "رعب": "👻", "رياضي": "⚽", "غموض": "🔍",
            "رومانسي": "💕", "تاريخي": "📜",
        }

        for genre in genres:
            emoji = genre_emojis.get(genre, "📌")
            prefix = "✅ " if genre in selected else ""
            builder.button(text=f"{prefix}{emoji} {genre}", callback_data=f"genre:toggle:{genre}")

        builder.adjust(2)

        builder.row(
            InlineKeyboardButton(text="🔍 تطبيق الفلتر", callback_data="search:apply_filters"),
            InlineKeyboardButton(text="🔄 مسح الكل", callback_data="genre:clear"),
        )
        builder.row(InlineKeyboardButton(text="🔙 للفلاتر", callback_data="search:filters"))

        return builder.as_markup()

    @staticmethod
    def search_results(query: str, results: list, page: int = 0):
        """results: [(series_id, title, match_score, total_eps, is_complete, avg_rating, rating_count), ...]"""
        builder = InlineKeyboardBuilder()

        if not results:
            builder.row(InlineKeyboardButton(text="😔 لا توجد نتائج", callback_data="ignore"))
        else:
            for row in results:
                sid, title, score = row[0], row[1], row[2]
                match_percent = int(score * 100)
                stars = "⭐" * min(5, max(1, int(score * 5)))

                builder.row(
                    InlineKeyboardButton(text=f"{stars} {title}", callback_data=f"s:{sid}"),
                    InlineKeyboardButton(text=f"{match_percent}%", callback_data=f"s:{sid}"),
                )

        builder.row(InlineKeyboardButton(text="💡 اقتراحات بحث", callback_data="search:suggestions"))
        builder.row(
            InlineKeyboardButton(text="🔍 بحث متقدم", callback_data="search:filters"),
            InlineKeyboardButton(text="🏠 الرئيسية", callback_data="main_menu"),
        )

        return builder.as_markup()
