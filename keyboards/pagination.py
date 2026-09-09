from aiogram.types import InlineKeyboardButton


def pagination_row(page: int, total_pages: int, callback_prefix: str):
    """
    يبني صف أزرار (السابق / رقم الصفحة / التالي) عام قابل لإعادة الاستخدام.
    مثال الاستخدام: pagination_row(0, 5, "page")  -> callback_data مثل 'page:1'
    """
    row = []
    if page > 0:
        row.append(InlineKeyboardButton(text="◀ السابق", callback_data=f"{callback_prefix}:{page-1}"))
    row.append(InlineKeyboardButton(text=f"📄 {page+1}/{max(1, total_pages)}", callback_data="ignore"))
    if page < total_pages - 1:
        row.append(InlineKeyboardButton(text="التالي ▶", callback_data=f"{callback_prefix}:{page+1}"))
    return row
