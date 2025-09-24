# myapp/views.py
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from twilio.twiml.messaging_response import MessagingResponse
import logging
import requests
from .supabase import supabase

logger = logging.getLogger("myapp")

@csrf_exempt
def upload_file(request):
    resp = MessagingResponse()

    try:
        if request.method != "POST":
            return HttpResponse("OK")

        from_number = request.POST.get("From", "")
        incoming_msg = request.POST.get("Body", "").strip().lower()
        num_media = int(request.POST.get("NumMedia", 0))

        logger.info(f"📩 Incoming message from {from_number}: {incoming_msg} | Media count: {num_media}")

        uploaded_files = []

        # Process media if any
        for i in range(num_media):
            media_url = request.POST.get(f"MediaUrl{i}")
            media_type = request.POST.get(f"MediaContentType{i}")
            filename = f"{from_number.replace(':','')}_{i}"

            # Determine file extension
            if "pdf" in media_type:
                filename += ".pdf"
            elif "image" in media_type:
                ext = media_type.split("/")[1]  # e.g., image/jpeg -> jpeg
                filename += f".{ext}"
            else:
                filename += ".dat"

            # Download the media
            try:
                r = requests.get(media_url, timeout=10)
                if r.status_code != 200:
                    logger.error(f"Failed to download media {media_url}, status {r.status_code}")
                    continue
            except Exception as e:
                logger.exception(f"Exception downloading media {media_url}: {e}")
                continue

            # Upload to Supabase
            try:
                data, error = supabase.storage.from_("images").upload(f"whatsapp/{filename}", r.content)
                if error:
                    logger.error(f"Failed to upload {filename} to Supabase: {error}")
                else:
                    uploaded_files.append(filename)
            except Exception as e:
                logger.exception(f"Exception uploading {filename} to Supabase: {e}")

        # Respond to user
        if uploaded_files:
            resp.message(f"✅ File(s) uploaded successfully: {', '.join(uploaded_files)}")
        else:
            # If no media, show default menu
            if incoming_msg in ["hi", "hello", "start", "menu", ""]:
                resp.message(
                    "👋 Welcome! You can send me a PDF or image to upload.\n"
                    "Or choose a topic:\n"
                    "1️⃣ Improve credit\n"
                    "2️⃣ Loan tips\n"
                    "3️⃣ Debt repayment\n"
                    "4️⃣ Common mistakes\n"
                    "5️⃣ Upload document"
                )
            else:
                resp.message("🤔 I didn't get that. Please reply with *menu* or send a file.")

        logger.info(f"✉️ Responding to {from_number}")
        return HttpResponse(str(resp))

    except Exception as e:
        logger.exception("Webhook failed:")
        return HttpResponse("Internal Server Error", status=500)
