from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

BOT_TOKEN = os.getenv("BOT_TOKEN")
LOGO_PATH = "logo.png"

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        pass

def run_health_server():
    server = HTTPServer(("0.0.0.0", 8080), HealthHandler)
    server.serve_forever()

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = None

    if update.message.video:
        file = await update.message.video.get_file()
        input_path = "input.mp4"
        output_path = "output.mp4"

    elif update.message.photo:
        file = await update.message.photo[-1].get_file()
        input_path = "input.jpg"
        output_path = "output.jpg"

    else:
        return

    await file.download_to_drive(input_path)

    # Add logo: resize to 25% of media width, center it, 50% opacity
    os.system(
        f'ffmpeg -y -i {input_path} -i {LOGO_PATH} '
        f'-filter_complex "[1:v]scale=iw*0.14:-1,format=rgba,colorchannelmixer=aa=0.5[logo];'
        f'[0:v][logo]overlay=(main_w-overlay_w)/2-200:(main_h-overlay_h)/2+370" '
        f'{output_path}'
    )

    # Send back
    if input_path.endswith(".mp4"):
        await update.message.reply_video(video=open(output_path, 'rb'))
    else:
        await update.message.reply_photo(photo=open(output_path, 'rb'))

# Start health check server in background thread
threading.Thread(target=run_health_server, daemon=True).start()

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.ALL, handle_media))

app.run_polling()
