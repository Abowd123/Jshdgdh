from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class EpisodePlayer:
    """أزرار التحكم أثناء مشاهدة الحلقة"""

    @staticmethod
    def player_controls(
        series_id: int,
        season: int,
        current_ep: int,
        has_prev: bool,
        has_next: bool,
        is_favorite: bool = False,
    ):
        builder = InlineKeyboardBuilder()

        nav_buttons = []
        if has_prev:
            nav_buttons.append(
                InlineKeyboardButton(
                    text="⏮ السابقة", callback_data=f"ep:{series_id}:{season}:{current_ep-1}"
                )
            )
        nav_buttons.append(
            InlineKeyboardButton(
                text="📋 قائمة الحلقات", callback_data=f"ep_list:{series_id}:{season}:0"
            )
        )
        if has_next:
            nav_buttons.append(
                InlineKeyboardButton(
                    text="التالية ⏭", callback_data=f"ep:{series_id}:{season}:{current_ep+1}"
                )
            )
        builder.row(*nav_buttons)

        builder.row(
            InlineKeyboardButton(
                text="⭐" if not is_favorite else "💛",
                callback_data=f"fav:add:{series_id}",
            ),
            InlineKeyboardButton(
                text="📝 تقييم", callback_data=f"rate:{series_id}:{season}:{current_ep}"
            ),
        )

        builder.row(
            InlineKeyboardButton(text="🔙 للموسم", callback_data=f"season:{series_id}:{season}"),
            InlineKeyboardButton(text="🏠 الرئيسية", callback_data="main_menu"),
        )

        return builder.as_markup()
