# myapp/views.py
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from twilio.twiml.messaging_response import MessagingResponse
import logging
from .supabase import supabase
import requests

logger = logging.getLogger("myapp")

@csrf_exempt
def upload_file(request):
    resp = MessagingResponse()
    try:
        if request.method == "POST":
            from_number = request.POST.get("From", "")
            incoming_msg = request.POST.get("Body", "").strip().lower()
            num_media = int(request.POST.get("NumMedia", 0))

            logger.info(f"📩 Incoming message from {from_number}: {incoming_msg} with {num_media} media files")

            uploaded_files = []

            # Process media files
            for i in range(num_media):
                media_url = request.POST.get(f"MediaUrl{i}")
                media_type = request.POST.get(f"MediaContentType{i}")
                filename = f"{from_number.replace(':', '')}_{i}"

                if "pdf" in media_type:
                    filename += ".pdf"
                elif "image" in media_type:
                    ext = media_type.split("/")[1]  # e.g., image/jpeg -> jpeg
                    filename += f".{ext}"
                else:
                    filename += ".dat"

                try:
                    r = requests.get(media_url, auth=(supabase.twilio_account_sid, supabase.twilio_auth_token))
                    if r.status_code == 200:
                        supabase.storage.from_("images").upload(f"whatsapp/{filename}", r.content)
                        uploaded_files.append(filename)
                        logger.info(f"✅ Uploaded file: {filename}")
                    else:
                        logger.error(f"Failed to download media {media_url}, status {r.status_code}")
                except Exception as e:
                    logger.exception(f"Exception downloading media {media_url}")

            if uploaded_files:
                resp.message(f"✅ File(s) uploaded successfully: {', '.join(uploaded_files)}\n📂 File submitted successfully!")
                return HttpResponse(str(resp))

            # Default menu response
            if incoming_msg in ["hi", "hello", "start", "menu", ""]:
                resp.message(
                    "👋 Welcome! You can send me a PDF or image to upload.\n"
                    "Or choose a topic:\n1️⃣ Improve credit\n2️⃣ Loan tips\n3️⃣ Debt repayment\n4️⃣ Common mistakes\n5️⃣ Upload document"
                )
            else:
                resp.message(
                    "🤔 I didn't get that. Please reply with *menu* or send a file."
                )

            return HttpResponse(str(resp))

        return HttpResponse("OK")

    except Exception as e:
        logger.exception("Webhook error:")
        return HttpResponse("Internal Server Error", status=500)
