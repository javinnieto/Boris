import requests
import os
import json

def send_telegram_message(bot_token, chat_id, text, reply_markup=None):
    """ Envia un mensaje de texto formateado en HTML o Markdown a Telegram """
    if not bot_token or not chat_id or bot_token == "YOUR_TELEGRAM_BOT_TOKEN":
        print("[Telegram Notifier] Token o Chat ID no configurado.")
        return None
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            res = r.json()
            return res.get("result", {}).get("message_id")
        else:
            print(f"[Telegram Error] HTTP {r.status_code}: {r.text}")
            return None
    except Exception as e:
        print(f"[Telegram Error] Excepción al enviar mensaje: {e}")
        return None

def edit_telegram_message(bot_token, chat_id, message_id, text, reply_markup=None):
    """ Edita el texto y botones de un mensaje enviado previamente """
    if not bot_token or not chat_id or not message_id:
        return False
    url = f"https://api.telegram.org/bot{bot_token}/editMessageText"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"[Telegram Error] Error editando mensaje: {e}")
        return False

def answer_callback_query(bot_token, callback_id, text=""):
    """ Responde a un clic de botón inline en Telegram """
    if not bot_token or not callback_id:
        return False
    url = f"https://api.telegram.org/bot{bot_token}/answerCallbackQuery"
    try:
        requests.post(url, json={"callback_query_id": callback_id, "text": text}, timeout=5)
        return True
    except Exception:
        return False

def send_telegram_document(bot_token, chat_id, file_path, caption=""):
    """ Envia un archivo (PDF, DOCX) al chat de Telegram """
    if not bot_token or not chat_id or bot_token == "YOUR_TELEGRAM_BOT_TOKEN":
        return False
        
    if not os.path.exists(file_path):
        print(f"[Telegram Notifier] Archivo no encontrado para envío: {file_path}")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    try:
        with open(file_path, 'rb') as doc:
            files = {'document': doc}
            data = {'chat_id': chat_id, 'caption': caption[:1024] if caption else ""}
            r = requests.post(url, data=data, files=files, timeout=30)
            return r.status_code == 200
    except Exception as e:
        print(f"[Telegram Error] Error enviando archivo {file_path}: {e}")
        return False

def send_job_alert_interactive(telegram_config, job_data, job_key):
    """
    Envía una alerta a Telegram con botones interactivos para que el usuario
    elija si desea generar CV Professional, CV Survival o Ignorar la oferta.
    """
    if not telegram_config.get("enabled", False):
        print(f"[Telegram Inactivo] Nueva oferta: {job_data['title']} en {job_data['company']}")
        return None

    bot_token = telegram_config.get("bot_token")
    chat_id = telegram_config.get("chat_id")
    
    title = job_data.get('title', 'Puesto no especificado')
    company = job_data.get('company', 'Empresa no especificada')
    job_url = job_data.get('url', '#')
    source = "Seek" if "seek.com" in job_url else "LinkedIn" if "linkedin.com" in job_url else "Portal Web"
    
    msg = (
        f"🚨 <b>NUEVA OFERTA PUBLICADA EN {source.upper()}</b>\n\n"
        f"📌 <b>Título:</b> {title}\n"
        f"🏢 <b>Empresa:</b> {company}\n"
        f"🔗 <a href='{job_url}'>Ver oferta completa en {source}</a>\n\n"
        f"👉 <i>¿Querés generar los documentos para esta oferta?</i>"
    )
    
    inline_keyboard = {
        "inline_keyboard": [
            [
                {"text": "💼 Generar CV Pro", "callback_data": f"pro:{job_key}"},
                {"text": "🛠️ Generar CV Survival", "callback_data": f"surv:{job_key}"}
            ],
            [
                {"text": "❌ Ignorar", "callback_data": f"ignore:{job_key}"}
            ]
        ]
    }
    
    return send_telegram_message(bot_token, chat_id, msg, reply_markup=inline_keyboard)

def notify_job_completed(telegram_config, job_data, output_folder, dm_text=""):
    """ Notifica que la generación de documentos finalizó y adjunta los PDFs si se activó """
    if not telegram_config.get("enabled", False):
        return

    bot_token = telegram_config.get("bot_token")
    chat_id = telegram_config.get("chat_id")
    send_docs = telegram_config.get("send_documents", True)
    
    title = job_data.get('title', 'Puesto no especificado')
    company = job_data.get('company', 'Empresa no especificada')
    job_url = job_data.get('url', '')
    
    source = "Seek" if "seek.com" in job_url else "LinkedIn" if "linkedin.com" in job_url else "Portal Web"
    link_html = f"🔗 <a href='{job_url}'><b>Postular en {source}</b></a>\n\n" if job_url else ""

    msg = (
        f"✅ <b>¡DOCUMENTOS LISTOS PARA POSTULAR!</b>\n\n"
        f"📌 <b>{title}</b> — <b>{company}</b>\n"
        f"{link_html}"
        f"📩 <b>Mensaje Directo (DM) listo para copiar:</b>\n"
        f"<code>{dm_text}</code>"
    )
    
    send_telegram_message(bot_token, chat_id, msg)
    
    if send_docs and os.path.exists(output_folder):
        for root, _, files in os.walk(output_folder):
            for file in sorted(files):
                # Enviar ÚNICAMENTE archivos .pdf (excluir .docx y .txt)
                if file.endswith('.pdf'):
                    fpath = os.path.join(root, file)
                    send_telegram_document(bot_token, chat_id, fpath, caption=f"📄 {file}")

def get_telegram_updates(bot_token, offset=0):
    """ Consulta la API de Telegram para obtener nuevos clics de botones o mensajes """
    if not bot_token or bot_token == "YOUR_TELEGRAM_BOT_TOKEN":
        return [], offset
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    params = {"offset": offset, "timeout": 2}
    try:
        r = requests.get(url, params=params, timeout=5)
        if r.status_code == 200:
            res = r.json().get("result", [])
            new_offset = offset
            for item in res:
                update_id = item.get("update_id", 0)
                if update_id >= new_offset:
                    new_offset = update_id + 1
            return res, new_offset
    except Exception:
        pass
    return [], offset
