import imaplib
import smtplib
import email
from email.mime.text import MIMEText
import google.generativeai as genai
import os
import traceback

print("1. Loading credentials...")
try:
    HOSTINGER_EMAIL = os.environ['EMAIL']
    HOSTINGER_PASS = os.environ['PASSWORD']
    GEMINI_API_KEY = os.environ['GEMINI_API_KEY']
except KeyError as e:
    print(f"CRITICAL ERROR: Missing GitHub Secret for {e}")
    exit(1)

print("2. Configuring Gemini AI...")
genai.configure(api_key=GEMINI_API_KEY)
system_prompt = """
You are the official AI Email Assistant for Angirus Ind Private Limited (angirusind.com).
Your goal is to answer incoming inquiries accurately and politely based ONLY on the following knowledge base:

[COMPANY & PRODUCT INFO]
- Legal Name: Angirus Ind Private Limited
- Location: Udaipur, Rajasthan, India | Email: info@angirusind.com
- Flagship Product: Wricks (Eco-friendly, lightweight, damp-proof bricks & blocks).
- Price: Approx. ₹18 per piece.

[GUARDRAILS]
1. Never invent discounts, MOQ rules, or custom shipping costs.
2. Sign off as:
Best regards,
Angirus Support Team
"""
model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=system_prompt)

print("3. Connecting to Hostinger IMAP (Receiving)...")
try:
    mail = imaplib.IMAP4_SSL("imap.hostinger.com", 993)
    mail.login(HOSTINGER_EMAIL, HOSTINGER_PASS)
    mail.select("inbox")

    status, messages = mail.search(None, "UNSEEN")
    email_ids = messages[0].split()
    
    if not email_ids:
        print("No unread emails found in the inbox.")
    else:
        print(f"Found {len(email_ids)} unread emails. Connecting to Hostinger SMTP (Sending)...")
        with smtplib.SMTP_SSL("smtp.hostinger.com", 465) as smtp_server:
            smtp_server.login(HOSTINGER_EMAIL, HOSTINGER_PASS)

            for e_id in email_ids:
                print(f"Processing email ID: {e_id}...")
                _, msg_data = mail.fetch(e_id, "(RFC822)")
                msg = email.message_from_bytes(msg_data[0][1])
                sender = msg.get("From")
                subject = str(msg.get("Subject"))

                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode(errors='ignore')
                            break
                else:
                    body = msg.get_payload(decode=True).decode(errors='ignore')

                print("Generating AI response...")
                prompt = f"Subject: {subject}\nSender: {sender}\nBody: {body}\n\nDraft a polite reply:"
                response = model.generate_content(prompt)
                ai_response = response.text

                print("Sending reply...")
                reply = MIMEText(ai_response)
                reply["Subject"] = f"Re: {subject}"
                reply["From"] = HOSTINGER_EMAIL
                reply["To"] = sender

                smtp_server.sendmail(HOSTINGER_EMAIL, sender, reply.as_string())
                print(f"SUCCESS: Replied to {sender}")

    mail.logout()
    print("Execution complete.")
except Exception as e:
    print("AN ERROR OCCURRED!")
    traceback.print_exc()
