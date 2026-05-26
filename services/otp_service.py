import os
import random
import time
import requests
from dotenv import load_dotenv

load_dotenv()

BREVO_API_KEY = os.getenv("BREVO_API_KEY")

otp_store = {}

def send_email_otp(email):

    otp = str(random.randint(1000, 9999))

    otp_store[email] = {
        "otp": otp,
        "time": time.time()
    }

    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }

    payload = {
        "sender": {
            "name": "ManoSamvada",
            "email": "manosamvad.app@gmail.com"
        },
        "to": [
            {
                "email": email
            }
        ],
        "subject": "Your OTP - ManoSamvada",
        "htmlContent":
            f"<h3>Your OTP is {otp}</h3>"
            f"<p>Valid for 5 minutes.</p>"
    }

    r = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        headers=headers,
        json=payload,
        timeout=15
    )

    print("Brevo:", r.status_code, r.text)

    if r.status_code >= 400:
        raise Exception(r.text)
