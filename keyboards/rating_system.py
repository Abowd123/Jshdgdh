from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class RatingSystem:
    """نظام التقييم بالنجوم"""

    @staticmethod
    def rate_episode(series_id: int, season: int, ep_number: int, current_rating: int = 0):
        builder = InlineKeyboardBuilder()

        stars_row = []
        for i in range(1, 6):
            star = "⭐" if i <= current_rating else "☆"
            stars_row.append(
                InlineKeyboardButton(
                    text=star, callback_data=f"rate_set:{series_id}:{season}:{ep_number}:{i}"
                )
            )
        builder.row(*stars_row)

        if current_rating > 0:
            builder.row(
                InlineKeyboardButton(text=f"تقييمك: {'⭐' * current_rating}", callback_data="ignore")
            )

        builder.row(
            InlineKeyboardButton(text="🔙 للحلقة", callback_data=f"ep:{series_id}:{season}:{ep_number}"),
            InlineKeyboardButton(text="🏠 الرئيسية", callback_data="main_menu"),
        )

        return builder.as_markup()

    @staticmethod
    def rating_stats(series_id: int, stats: dict):
        """stats: {'average': float, 'total_votes': int, 'distribution': {1: n, ...}}"""
        builder = InlineKeyboardBuilder()

        avg_stars = "⭐" * round(stats["average"])
        builder.row(
            InlineKeyboardButton(text=f"المتوسط: {avg_stars} ({stats['average']:.1f})", callback_data="ignore")
        )
        builder.row(
            InlineKeyboardButton(text=f"👥 عدد المصوتين: {stats['total_votes']}", callback_data="ignore")
        )

        for stars in range(5, 0, -1):
            count = stats["distribution"].get(stars, 0)
            percentage = (count / stats["total_votes"] * 100) if stats["total_votes"] > 0 else 0
            bar = "█" * int(percentage / 10)
            builder.row(
                InlineKeyboardButton(
                    text=f"{'⭐' * stars} {bar} {count} ({percentage:.1f}%)", callback_data="ignore"
                )
            )

        builder.row(InlineKeyboardButton(text="🔙 للمسلسل", callback_data=f"s:{series_id}"))

        return builder.as_markup()
