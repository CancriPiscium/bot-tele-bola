import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from google import genai
from google.genai import types
from duckduckgo_search import DDGS
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# 1. Inisialisasi API Key & Chat ID
TELEGRAM_TOKEN = "8985712066:AAHS4DuoBgpqQGQ9ba_sHnPpNjkp3-sIsc8"
GEMINI_API_KEY = "AQ.Ab8RN6LJkRmkX3R59ABKQ2sxnKn_wyazxqbIuOIFhbUQGGzXTw"

# CHAT ID Kamu
MY_CHAT_ID = 1409170184  

client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_INSTRUCTION = (
    "Kamu adalah bot Telegram pakar sepak bola dunia dengan kepribadian anak SMA/tongkrongan "
    "yang songong, tengil, gampang emosi, gak sabaran, dan ceplos-ceplos. "
    "Pengetahuan kamu sangat luas tentang sepak bola (liga top Eropa, rumor transfer, taktik, sampai drama pemain/klub).\n\n"
    "ATURAN GAYA BICARA & RESPON:\n"
    "1. Jawab setiap pertanyaan atau rangkuman berita secara singkat, padat, to the point, dan akurat.\n"
    "2. Gunakan bahasa gaul anak tongkrongan (contoh: 'gw', 'lu', 'mikir napa', 'kepo amat', 'debat mulu', 'kocak lu').\n"
    "3. Nada bicara wajib sinis, tengil, sok tau (tapi jawabannya faktual benar), dan langsung ngeledek kalau ada kesempatan.\n"
    "4. Kalau pengguna nanya hal sepele atau polos, semprot dulu baru kasih jawabannya.\n"
    "5. Kalau pengguna nanya hal DI LUAR sepak bola, ledek dan suruh nanya soal bola aja (misal: 'Dikiranya gw gugel apa? Nanya bola aja lu!').\n"
    "6. Jangan pakai bahasa formal, pembukaan yang manis (kayak 'Halo!'), atau kata penutup santun.\n"
    "7. Sangat jarang atau JANGAN pakai emoji sama sekali."
)

# Fix Syntax Error di logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Fungsi mengambil berita bola terbaru dari internet
def get_latest_football_news():
    try:
        results = DDGS().text("latest top football news world", max_results=5)
        news_text = "\n".join([f"- {r['title']}: {r['body']}" for r in results])
        return news_text
    except Exception as e:
        print(f"Gagal ambil berita: {e}")
        return "Gagal mengambil data berita terbaru."

# Fungsi otomatis yang akan berjalan setiap hari
async def send_daily_news_job(context: ContextTypes.DEFAULT_TYPE):
    if not MY_CHAT_ID or MY_CHAT_ID == 123456789:
        print("Chat ID belum diatur di variabel MY_CHAT_ID!")
        return

    raw_news = get_latest_football_news()
    prompt = f"Berikut adalah berita bola terbaru hari ini:\n{raw_news}\n\nRangkum berita di atas jadi rangkuman harian ter-hits dengan gaya tengil kamu!"

    models_to_try = ['gemini-3.6-flash', 'gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash']
    
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                ),
            )
            ai_reply = response.text
            await context.bot.send_message(chat_id=MY_CHAT_ID, text=ai_reply)
            return
        except Exception as e:
            print(f"Gagal pakai {model_name} saat job harian: {e}")
            continue

# --- FUNGSI 2: Merespons Chat Biasa dari Pengguna ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    models_to_try = ['gemini-3.6-flash', 'gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash']
    
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=user_text,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                ),
            )
            ai_reply = response.text
            await update.message.reply_text(ai_reply)
            return
        except Exception as e:
            print(f"Model {model_name} gagal/sibuk ({e}), mencoba model berikutnya...")
            continue

    await update.message.reply_text("Dahlah, servernya lagi down/penuh. Malas gw sama lu, coba entar lagi.")

# Inisialisasi scheduler di dalam event loop Telegram
async def post_init(application):
    scheduler = AsyncIOScheduler()
    # Atur jam pengiriman otomatis (Contoh: Jam 07:00 pagi)
    scheduler.add_job(
        send_daily_news_job,
        'cron',
        hour=7,
        minute=0,
        args=[application]
    )
    scheduler.start()
    print("Scheduler otomatis berhasil diaktifkan.")

# Command /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        f"Ngapain nge-start? Nih Chat ID lu: `{chat_id}`.\n"
        "Mau nanya bola apa lu? Atau mau nunggu rangkuman harian dari gw?",
        parse_mode="Markdown"
    )

# Command /myid untuk mengecek ID Telegram
async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Chat ID lu: `{update.effective_chat.id}`", parse_mode="Markdown")

# Main Application
if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('myid', my_id))
    
    # Menambahkan handler agar bot merespons chat pesan biasa
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Bot Agent Berita & Chat Otomatis sedang berjalan...")
    app.run_polling()