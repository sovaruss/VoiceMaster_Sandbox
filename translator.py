import re
from deep_translator import GoogleTranslator

def is_mixed(text):
    has_ru = bool(re.search('[а-яА-ЯёЁ]', text))
    has_en = bool(re.search('[a-zA-Z]', text))
    return has_ru and has_en

def is_russian(text):
    return bool(re.search('[а-яА-ЯёЁ]', text))

def translate_text(text, target):
    try:
        return GoogleTranslator(source='auto', target=target).translate(text)
    except:
        return text

def split_text_by_lang(text):
    """Разбивает текст на части RU и EN для смешанной озвучки"""
    return re.findall(r'[а-яА-ЯёЁ\s\d.,!?-]+|[a-zA-Z\s\d.,!?-]+', text)