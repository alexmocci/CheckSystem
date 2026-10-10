
import os

import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_telegram_notification(event):
    """Invia un evento CheckSystem tramite Telegram."""

    if not BOT_TOKEN or not CHAT_ID:
        print(
            "Telegram non configurato: "
            "controlla TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID nel file .env"
        )
        return False

    if event["event_type"] == "ALERT":
        title = "CHECKSYSTEM - ALLARME"
    elif event["event_type"] == "RECOVERED":
        title = "CHECKSYSTEM - RIPRISTINO"
    else:
        title = "CHECKSYSTEM - EVENTO"

    message = (
        f"{title}\n\n"
        f"Indicatore: {event['metric']}\n"
        f"{event['details']}\n"
        f"Data: {event['timestamp']}"
    )

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    try:
        response = requests.post(
            url,
            json={
                "chat_id": CHAT_ID,
                "text": message,
            },
            timeout=10,
        )
        response.raise_for_status()

        if not response.json().get("ok", False):
            print("Telegram non ha confermato l'invio.")
            return False

        print(f"Notifica Telegram inviata: {event['event_type']}")
        return True

    except (requests.RequestException, ValueError):
        # Non stampiamo l'eccezione per non esporre il token nell'URL.
        print("Errore nell'invio Telegram. Controlla configurazione e rete.")
        return False
