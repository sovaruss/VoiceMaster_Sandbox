from deep_translator import GoogleTranslator
import re

def is_russian(text):
    return bool(re.search('[а-яА-Я]', text))

def is_mixed(text):
    has_ru = bool(re.search('[а-яА-Я]', text))
    has_en = bool(re.search('[a-zA-Z]', text))
    return has_ru and has_en

def translate_text(text, target_lang):
    """
    Пытается перевести текст. Если перевод не удался или вернул оригинал,
    пробует сменить параметры.
    """
    try:
        clean_text = text.strip()
        if not clean_text:
            return text
            
        # Попытка 1: Автоматическое определение
        translator = GoogleTranslator(source='auto', target=target_lang)
        translated = translator.translate(clean_text)
        
        # Попытка 2: Если текст не изменился, а должен был (для смешанного или чужого языка)
        if translated == clean_text:
            alt_source = 'en' if target_lang == 'ru' else 'ru'
            translated = GoogleTranslator(source=alt_source, target=target_lang).translate(clean_text)
             
        return translated
    except Exception as e:
        print(f"!!! Ошибка в translator.py: {e}")
        return text