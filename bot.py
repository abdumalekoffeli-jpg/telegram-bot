import os
import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import yt_dlp

BOT_TOKEN = "8934461282:AAHmBq-KpC5iDSAK3S_I1_TvhliLKTm2uRI"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        "Salom! Musiqa va Video yuklovchi botga xush kelibsiz! 🎵\n\n"
        "• Qo'shiqchi yoki qo'shiq nomini yozing (variantlar chiqadi).\n"
        "• Instagram yoki YouTube havolasini yuboring (video va musiqasi avtomatik keladi)."
    )

@dp.message(F.text.startswith("http://") | F.text.startswith("https://"))
async def handle_link(message: types.Message):
    url = message.text.strip()
    status_msg = await message.answer("📥 Video va musiqa yuklab olinmoqda, biroz kuting...")
    
    user_id = message.from_user.id
    vid_file = f"video_{user_id}.mp4"
    aud_file = f"audio_{user_id}.mp3"
    
    try:
        loop = asyncio.get_event_loop()
        
        # 1. Videoni yuklash
        ydl_opts_vid = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': vid_file,
            'quiet': True,
            'noplaylist': True
        }
        def download_vid():
            with yt_dlp.YoutubeDL(ydl_opts_vid) as ydl:
                ydl.download([url])
        await loop.run_in_executor(None, download_vid)
        
        # 2. Musiqani o'rib olish (MP3)
        ydl_opts_aud = {
            'format': 'bestaudio/best',
            'outtmpl': f"audio_{user_id}.%(ext)s",
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'noplaylist': True
        }
        def download_aud():
            with yt_dlp.YoutubeDL(ydl_opts_aud) as ydl:
                ydl.download([url])
        await loop.run_in_executor(None, download_aud)
        
        # Fayllarni yuborish
        if os.path.exists(vid_file):
            await message.answer_video(video=types.FSInputFile(vid_file), caption="🎬 Video")
        if os.path.exists(aud_file):
            await message.answer_audio(audio=types.FSInputFile(aud_file), caption="🎵 Musiqa")
            
        await status_msg.delete()
        
    except Exception as e:
        await status_msg.edit_text("❌ Yuklab olishda xatolik yuz berdi.")
    finally:
        if os.path.exists(vid_file):
            os.remove(vid_file)
        if os.path.exists(aud_file):
            os.remove(aud_file)

@dp.message(F.text)
async def search_music(message: types.Message):
    query = message.text.strip()
    status_msg = await message.answer(f"🔎 <b>'{query}'</b> bo'yicha qidirilmoqda...", parse_mode="HTML")

    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'default_search': 'ytsearch5',
    }

    try:
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(query, download=False))

        entries = info.get('entries', [])
        if not entries:
            await status_msg.edit_text("❌ Hech narsa topilmadi.")
            return

        buttons = []
        for i, entry in enumerate(entries[:5], start=1):
            title = entry.get('title', 'Noma\'lum')[:35]
            duration = entry.get('duration', 0)
            mins, secs = divmod(duration, 60)
            time_str = f"{mins}:{secs:02d}" if duration else ""
            
            btn_text = f"{i}. {title} [{time_str}]"
            buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"song_{entry['id']}")])

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await status_msg.edit_text("👇 Kerakli qo'shiqni tanlang:", reply_markup=keyboard)

    except Exception as e:
        await status_msg.edit_text("❌ Qidiruvda xatolik yuz berdi.")
@dp.callback_query(F.data.startswith("song_"))
async def download_chosen_song(callback: CallbackQuery):
    song_id = callback.data.split("song_")[1]
    url = f"https://www.youtube.com/watch?v={song_id}"
    
    await callback.message.edit_text("📥 Musiqa yuklanmoqda, kuting...")

    file_name = f"music_{song_id}.mp3"
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f"music_{song_id}.%(ext)s",
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'noplaylist': True
    }

    try:
        loop = asyncio.get_event_loop()
        def download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        await loop.run_in_executor(None, download)

        audio_file = types.FSInputFile(file_name)
        await callback.message.answer_audio(audio=audio_file, caption="🎵 Musiqa")
        await callback.message.delete()

    except Exception as e:
        await callback.message.answer("❌ Yuklashda xatolik bo'ldi.")
    finally:
        if os.path.exists(file_name):
            os.remove(file_name)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    print("Bot muvaffaqiyatli ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())