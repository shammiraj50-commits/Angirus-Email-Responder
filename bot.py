import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from google import genai
import os

# 1. Load Credentials
HOSTINGER_EMAIL = os.environ['EMAIL']
HOSTINGER_PASS = os.environ['PASSWORD']
GEMINI_API_KEY = os.environ['GEMINI_API_KEY']

# 2. Configure the AI Model
client = genai.Client(api_key=GEMINI_API_KEY)
model_id = 'gemini-1.5-flash'
system_prompt = """
You are the official AI Email Assistant for Angirus Ind Private Limited.
Your goal is to answer inquiries based on the company's knowledge base. 
Products: Wricks (Eco-friendly, lightweight, damp-proof bricks).
Price: Approx. ₹18 per piece.
Never invent discounts, bulk pricing, or custom shipping costs. Route complex queries to human staff.
"""

# 3. Connect to Hostinger Webmail (IMAP)
try:
    mail = imaplib.IMAP4_SSL("imap.hostinger.com", 993)
    mail.login(HOSTINGER_EMAIL, HOSTINGER_PASS)
    mail.select("inbox")

    # 4. Search for Unread Emails
    status, messages = mail.search(None, "UNSEEN")
    email_ids = messages[0].split()

    if email_ids:
        # Connect to Hostinger Outbox (SMTP)
        with smtplib.SMTP_SSL("smtp.hostinger.com", 465) as smtp_server:
            smtp_server.login(HOSTINGER_EMAIL, HOSTINGER_PASS)

            for e_id in email_ids:
                # Fetch and parse the email
                _, msg_data = mail.fetch(e_id, "(RFC822)")
                msg = email.message_from_bytes(msg_data[0][1])
                sender = msg.get("From")
                subject = str(msg.get("Subject"))
                
                # Extract text body
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode(errors='ignore')
                            break
                else:
                    body = msg.get_payload(decode=True).decode(errors='ignore')

                # Generate the AI Response
                prompt = f"Subject: {subject}\nSender: {sender}\nBody: {body}\n\nDraft a polite reply:"
                response = client.models.generate_content(
                    model=model_id,
                    contents=prompt,
                    config={"system_instruction": system_prompt}
                )
                ai_response = response.text
                
                # Send the Reply
                reply = MIMEText(ai_response)
                reply["Subject"] = f"Re: {subject}"
                reply["From"] = HOSTINGER_EMAIL
                reply["To"] = sender
                
                smtp_server.sendmail(HOSTINGER_EMAIL, sender, reply.as_string())
                
    mail.logout()
except Exception as e:
    print(f"An error occurred: {e}")
