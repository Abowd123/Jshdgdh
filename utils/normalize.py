import re


def normalize_arabic(text: str) -> str:
    """تطبيع النص العربي للبحث: توحيد الألف/الياء/التاء المربوطة وإزالة التشكيل."""
    if not text:
        return ""

    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    text = text.replace("ى", "ي").replace("ئ", "ي").replace("ؤ", "و")
    text = text.replace("ة", "ه")

    # إزالة التشكيل
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text)

    # إزالة المسافات الزائدة
    text = re.sub(r"\s+", " ", text).strip()

    return text
