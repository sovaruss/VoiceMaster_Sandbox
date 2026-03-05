import asyncio, os, database, translator, voice_engine, archiver, file_reader, config
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()
user_data = {}

# КЛАВИАТУРЫ
def kb_modes():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎧 Обычная озвучка", callback_data="m_norm"),
         InlineKeyboardButton(text="🥪 Режим Сэндвич", callback_data="m_sand")]
    ])

def kb_mixed():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 RU", callback_data="l_ru"),
         InlineKeyboardButton(text="🇺🇸 EN", callback_data="l_en"),
         InlineKeyboardButton(text="🎭 RU-EN", callback_data="l_mix")]
    ])

def kb_gender():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👩 Женский", callback_data="g_female"),
         InlineKeyboardButton(text="👨 Мужской", callback_data="g_male")]
    ])

def kb_standard_4():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Жен", callback_data="f_ru_female"), InlineKeyboardButton(text="🇷🇺 Муж", callback_data="f_ru_male")],
        [InlineKeyboardButton(text="🇺🇸 Жен", callback_data="f_en_female"), InlineKeyboardButton(text="🇺🇸 Муж", callback_data="f_en_male")]
    ])

@dp.message(Command("start"))
async def start(m: types.Message):
    await m.answer("Напишите текст или пришлите файлы (txt, docx, pdf, epub)")

@dp.message(F.text | F.document)
async def handle_input(m: types.Message):
    text = m.text
    fname = None
    if m.document:
        fname = m.document.file_name
        path = f"tmp_{fname}"
        await bot.download_file((await bot.get_file(m.document.file_id)).file_path, path)
        text = file_reader.get_text_from_file(path, fname.split('.')[-1].lower())
        os.remove(path)
    
    if not text: return
    user_data[m.from_user.id] = {'text': text, 'fname': fname}
    await m.answer("⚙️ Выберите режим:", reply_markup=kb_modes())

@dp.callback_query(F.data.startswith("m_"))
async def select_mode(c: types.CallbackQuery):
    uid = c.from_user.id
    mode = c.data.split("_")[1]
    user_data[uid]['mode'] = mode
    
    if mode == "sand":
        await c.message.edit_text("🥪 Выберите пол:", reply_markup=kb_gender())
    else:
        if translator.is_mixed(user_data[uid]['text']):
            await c.message.edit_text("В вашем тексте разные языки, что вы хотите выбрать?", reply_markup=kb_mixed())
        else:
            await c.message.edit_text("🗣 Выберите голос:", reply_markup=kb_standard_4())

@dp.callback_query(F.data.startswith("l_"))
async def select_lang_mixed(c: types.CallbackQuery):
    user_data[c.from_user.id]['lang_choice'] = c.data.split("_")[1]
    await c.message.edit_text("🗣 Выберите пол:", reply_markup=kb_gender())

@dp.callback_query(F.data.startswith("g_") | F.data.startswith("f_"))
async def finalize(c: types.CallbackQuery):
    uid = c.from_user.id
    if uid not in user_data: return
    data = user_data[uid]
    
    wait_msg = await c.message.answer("⏳ Обработка...")
    await c.message.delete()
    
    ts = datetime.now().strftime("%H%M%S")
    name_base = os.path.splitext(data['fname'])[0] if data['fname'] else "VoiceMaster"
    f_audio = f"{name_base}_{ts}.mp3"
    
    try:
        audio = voice_engine.AudioSegment.empty()
        is_tr = False
        gender = c.data.split("_")[-1]
        status = ""
        trans_res = ""

        if data['mode'] == 'norm':
            if 'lang_choice' in data: # СМЕШАННЫЙ ТЕКСТ (Блок 1)
                choice = data['lang_choice']
                if choice == 'mix':
                    status = "RU-EN"
                    audio = await voice_engine.generate_mixed(data['text'], gender)
                else:
                    # ВОТ ТУТ ИСПРАВЛЕНИЕ: Переводим ВЕСЬ текст целиком
                    status = choice.upper()
                    trans_res = translator.translate_text(data['text'], choice)
                    audio = await voice_engine.get_seg(trans_res, f"{choice}_{gender}")
                    is_tr = True
            else: # ОБЫЧНЫЙ ТЕКСТ (4 кнопки)
                v_key = c.data.replace("f_", "")
                target_lang = v_key.split("_")[0]
                status = target_lang.upper()
                
                # Если текст на одном языке, а выбрали кнопку другого — переводим
                if (target_lang == 'ru' and not translator.is_russian(data['text'])) or \
                   (target_lang == 'en' and translator.is_russian(data['text'])):
                    trans_res = translator.translate_text(data['text'], target_lang)
                    audio = await voice_engine.get_seg(trans_res, v_key)
                    is_tr = True
                else:
                    audio = await voice_engine.get_seg(data['text'], v_key)
        else:
            # РЕЖИМ СЭНДВИЧ
            status = "Sandwich"
            ratio = database.get_pause(uid)
            full_translation = []
            for line in data['text'].split('\n'):
                if not line.strip(): continue
                target_lang = 'en' if translator.is_russian(line) else 'ru'
                tr = translator.translate_text(line, target_lang)
                full_translation.append(tr)
                s_o = await voice_engine.get_seg(line, f"{'ru' if target_lang=='en' else 'en'}_{gender}")
                s_t = await voice_engine.get_seg(tr, f"{target_lang}_{gender}")
                audio += voice_engine.make_sandwich(s_o, s_t, ratio)
            trans_res = "\n".join(full_translation)
            is_tr = True 

        audio.export(f_audio, format="mp3")
        await wait_msg.delete()
        
        caption = f"✅Символов: {len(data['text'])},   {status}"
        await bot.send_voice(uid, FSInputFile(f_audio), caption=caption)

        if is_tr:
            user_data[uid]['original'] = data['text']
            user_data[uid]['translated'] = trans_res
            kb_zip = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Да", callback_data="z_y"), 
                 InlineKeyboardButton(text="❌ Нет", callback_data="z_n")]
            ])
            await bot.send_message(uid, "📦 Создать ZIP с переводом?", reply_markup=kb_zip)
        else:
            del user_data[uid]

    except Exception as e: 
        print(f"Error: {e}")
    finally:
        if os.path.exists(f_audio): os.remove(f_audio)

@dp.callback_query(F.data.startswith("z_"))
async def handle_zip(c: types.CallbackQuery):
    uid = c.from_user.id
    if c.data == "z_y" and uid in user_data:
        pz = archiver.create_zip(user_data[uid]['original'], user_data[uid]['translated'], user_data[uid]['fname'])
        await c.message.answer_document(FSInputFile(pz))
        if os.path.exists(pz): os.remove(pz)
    await c.message.delete()
    if uid in user_data: del user_data[uid]

async def main():
    database.init_db()
    print("🚀 Бот запущен И ОБНОВЛЁН!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())