import edge_tts
from pydub import AudioSegment
import io, os, translator

VOICES = {
    'ru_female': 'ru-RU-SvetlanaNeural', 'ru_male': 'ru-RU-DmitryNeural',
    'en_female': 'en-US-JennyNeural', 'en_male': 'en-US-GuyNeural'
}

async def get_seg(text, voice_key):
    voice = VOICES.get(voice_key, voice_key)
    comm = edge_tts.Communicate(text, voice)
    data = b""
    async for chunk in comm.stream():
        if chunk["type"] == "audio": data += chunk["data"]
    
    if not data: return AudioSegment.silent(duration=100)
    return AudioSegment.from_file(io.BytesIO(data), format="mp3")

async def generate_mixed(text, gender):
    """Блок 1: Озвучка 'как в тексте' разными голосами"""
    res = AudioSegment.empty()
    for part in translator.split_text_by_lang(text):
        if not part.strip(): continue
        v = f"ru_{gender}" if translator.is_russian(part) else f"en_{gender}"
        res += await get_seg(part, v)
    return res

def make_sandwich(orig, trans, ratio):
    """Блок 2: Оригинал -> Пауза -> Перевод -> Пауза -> Оригинал"""
    p_ms = int(len(orig) * (ratio / 100))
    p = AudioSegment.silent(duration=p_ms)
    return orig + p + trans + p + orig + (p * 2)