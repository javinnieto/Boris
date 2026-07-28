"""
test_telegram.py — Verifica permisos y notificaciones interactivas del bot de Telegram.

Uso:
    python scripts/test_telegram.py
    (desde la raíz del proyecto)
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "bot"))
import telegram_notifier


def test_bot():
    print("=== TEST DE NOTIFICACIÓN INTERACTIVA EN TELEGRAM ===")

    config_path = os.path.join(ROOT, "data", "search_config.json")
    if not os.path.exists(config_path):
        print(f"Error: No se encontró {config_path}")
        return

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    telegram = config.get("telegram", {})
    token    = telegram.get("bot_token", "")
    chat_id  = telegram.get("chat_id", "")

    if not telegram.get("enabled") or token == "YOUR_TELEGRAM_BOT_TOKEN":
        print("\n[!] Telegram no está activado en data/search_config.json.")
        print("Editá el archivo y configurá:")
        print('  "enabled": true,')
        print('  "bot_token": "TU_TOKEN_DE_BOTFATHER",')
        print('  "chat_id":   "TU_CHAT_ID"')
        return

    print(f"\nEnviando mensaje de prueba al chat ID: {chat_id}...")

    job_data = {
        "title":   "Mechanical Engineer (Prueba Bot)",
        "company": "Empresa de Prueba Pty Ltd",
        "url":     "https://www.seek.com.au",
    }

    msg_id = telegram_notifier.send_job_alert_interactive(telegram, job_data, "test_job_001")

    if msg_id:
        print("\n✅ ¡ÉXITO! Mensaje enviado correctamente a Telegram.")
        print(f"   Message ID: {msg_id}")
        print("\nDeberías ver en tu Telegram:")
        print("  [ 💼 Generar CV Pro ]  [ 🛠️ Generar CV Survival ]  [ ❌ Ignorar ]")
    else:
        print("\n❌ Error al enviar el mensaje. Verificá:")
        print("  1. ¿Le diste /start a tu bot en Telegram?")
        print("  2. ¿El bot_token y chat_id en data/search_config.json son correctos?")


if __name__ == "__main__":
    test_bot()
