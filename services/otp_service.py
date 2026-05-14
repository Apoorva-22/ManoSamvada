import os
import random
import smtplib
import time
from dotenv import load_dotenv

load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

otp_store = {}

# ---------- EMAIL OTP ----------
def send_email_otp(email):
    otp = str(random.randint(1000, 9999))

    otp_store[email] = {
        "otp": otp,
        "time": time.time()
    }

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.ehlo()

        server.login(EMAIL_USER, EMAIL_PASS)

        server.sendmail(
            EMAIL_USER,
            email,
            f"Your OTP is {otp}"
        )

        server.quit()
        print("OTP:", otp)

    except Exception as e:
        print("Email Error:", e)

