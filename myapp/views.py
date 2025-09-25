# myapp/views.py
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from twilio.twiml.messaging_response import MessagingResponse
import logging
import requests

from .supabase import supabase
from .twilio import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN

logger = logging.getLogger("myapp")

@csrf_exempt
def upload_file(request):
    resp = MessagingResponse()
    try:
        if request.method == "POST":
            from_number = request.POST.get("From", "")
            incoming_msg = request.POST.get("Body", "").strip().lower()
            num_media = int(request.POST.get("NumMedia", 0))

            logger.info(f"📩 Incoming message from {from_number}: {incoming_msg}, NumMedia={num_media}")

            uploaded_files = []

            # Process media if any
            for i in range(num_media):
                media_url = request.POST.get(f"MediaUrl{i}")
                media_type = request.POST.get(f"MediaContentType{i}")
                filename = f"{from_number.replace(':','')}_{i}"

                # Keep file extension
                if "pdf" in media_type:
                    filename += ".pdf"
                elif "image" in media_type:
                    ext = media_type.split("/")[1]  # image/jpeg -> jpeg
                    filename += f".{ext}"
                else:
                    filename += ".dat"

                # Download the media using Twilio auth
                r = requests.get(media_url, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))
                if r.status_code == 200:
                    supabase.storage.from_("uploads").upload(f"whatsapp/{filename}", r.content)
                    uploaded_files.append(filename)
                else:
                    logger.error(f"Failed to download media {media_url}, status {r.status_code}")

            if uploaded_files:
                resp.message(f"✅ File(s) submitted successfully: ")
                return HttpResponse(str(resp))

            # Default menu response if no media
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
                resp.message(
                    "🤔 I didn't get that. Please reply with *menu* or send a file."
                )

            logger.info(f"✉️ Sending response to {from_number}")
            return HttpResponse(str(resp))

        return HttpResponse("OK")

    except Exception as e:
        logger.exception("Webhook error:")
        return HttpResponse("Internal Server Error", status=500)
