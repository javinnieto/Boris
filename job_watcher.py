"""
job_watcher.py — Daemon de monitoreo de empleos e integración con Telegram.

Flujo:
  1. Cada N minutos escanea Seek y LinkedIn según search_config.json.
  2. Por cada oferta nueva, envía una notificación a Telegram con 3 botones:
       [ 💼 Generar CV Pro ]  [ 🛠️ Generar CV Survival ]  [ ❌ Ignorar ]
  3. En un loop paralelo escucha clics del usuario y ejecuta:
       python main.py <URL> --pro|--survival --creativity 1 --notify
     lo que genera CV + Cover Letter + DM y los envía de vuelta por Telegram.

Uso:
    python job_watcher.py          # monitoreo continuo
    python job_watcher.py --once   # un solo ciclo de escaneo (útil para tests)
"""

import os
import sys
import time
import json
import subprocess
from urllib.parse import quote
from bs4 import BeautifulSoup
import requests

# ── Rutas del proyecto ────────────────────────────────────────────────────────
ROOT       = os.path.dirname(os.path.abspath(__file__))
BOT_DIR    = os.path.join(ROOT, "bot")
DATA_DIR   = os.path.join(ROOT, "data")
MAIN_PY    = os.path.join(ROOT, "main.py")

sys.path.insert(0, BOT_DIR)
import telegram_notifier

try:
    from curl_cffi import requests as crequests
except ImportError:
    crequests = requests

# ── Helpers JSON ─────────────────────────────────────────────────────────────

def load_json(path, default=None):
    if not os.path.exists(path):
        return {} if default is None else default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[Watcher] Error cargando {path}: {e}")
        return {} if default is None else default

def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Watcher] Error guardando {path}: {e}")

# ── Scrapers de búsqueda ──────────────────────────────────────────────────────

def is_within_max_age(date_str, max_age_minutes=30):
    """
    Verifica si una cadena de texto de fecha (ej. "5m ago", "15m ago", "1h ago", "2d ago")
    está dentro del límite de minutos especificado.
    """
    if not date_str:
        return True
    d = date_str.lower().strip()
    if "m" in d and "ago" in d:
        try:
            mins = int(d.split("m")[0].strip())
            return mins <= max_age_minutes
        except ValueError:
            return True
    if "h" in d or "d" in d or "day" in d or "hour" in d:
        return False
    return True

def fetch_seek_jobs(keyword, location, max_results=10, max_age_minutes=30):
    url = f"https://www.seek.com.au/jobs?keywords={quote(keyword)}&where={quote(location)}&sortmode=CreatedAt"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0"}
    jobs = []
    try:
        r = crequests.get(url, impersonate="chrome120", timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            for art in soup.find_all("article")[:max_results]:
                title_elem   = art.find(attrs={"data-automation": "jobTitle"}) or art.find("a")
                company_elem = art.find(attrs={"data-automation": "jobCompany"})
                date_elem    = art.find(attrs={"data-automation": "jobListingDate"})
                
                if not title_elem:
                    continue
                raw_href = title_elem.get("href", "")
                if "/job/" not in raw_href:
                    continue
                    
                date_text = date_elem.text.strip() if date_elem else ""
                if max_age_minutes and date_text:
                    if not is_within_max_age(date_text, max_age_minutes):
                        continue

                job_id = raw_href.split("/job/")[1].split("?")[0]
                jobs.append({
                    "id":        f"seek_{job_id}",
                    "title":     title_elem.text.strip(),
                    "company":   company_elem.text.strip() if company_elem else "Empresa",
                    "url":       f"https://www.seek.com.au/job/{job_id}",
                    "source":    "seek",
                    "posted_at": date_text
                })
    except Exception as e:
        print(f"[Seek] Error: {e}")
    return jobs


def fetch_linkedin_jobs(keyword, location, max_results=10, max_age_minutes=30):
    # LinkedIn Guest API: f_TPR en segundos (30 min = 1800 seg, 60 min = 3600 seg)
    tpr_seconds = (max_age_minutes * 60) if max_age_minutes else 86400
    url = (
        f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
        f"?keywords={quote(keyword)}&location={quote(location)}&f_TPR=r{tpr_seconds}&start=0"
    )
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0",
        "Accept":     "text/html,application/xhtml+xml",
    }
    jobs = []
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            for card in soup.find_all("li")[:max_results]:
                a_tag = card.find("a", class_="base-card__full-link")
                if not a_tag:
                    continue
                full_link = a_tag.get("href", "").split("?")[0]
                job_id    = full_link.strip("/").split("-")[-1]
                comp_elem = card.find("h4", class_="base-search-card__subtitle")
                time_elem = card.find("time")
                date_text = time_elem.text.strip() if time_elem else ""

                jobs.append({
                    "id":        f"linkedin_{job_id}",
                    "title":     a_tag.text.strip(),
                    "company":   comp_elem.text.strip() if comp_elem else "Empresa",
                    "url":       full_link,
                    "source":    "linkedin",
                    "posted_at": date_text
                })
    except Exception as e:
        print(f"[LinkedIn] Error: {e}")
    return jobs

def is_job_relevant_for_rule(job, rule):
    """
    Filtra estrictamente ofertas irrelevantes (Senior, Lead, Pharma, Medical, fuera de dominio, o no-entry level).
    """
    title = job.get("title", "").lower()
    company = job.get("company", "").lower()

    exclude_keywords = [k.lower() for k in rule.get("exclude_keywords", [])]
    require_domain = [k.lower() for k in rule.get("require_any_domain_keyword", [])]

    # 1. Descartar si el título contiene palabras excluidas (Senior, Sr, Lead, Pharma, Medical, etc.)
    for exc in exclude_keywords:
        if exc in title:
            print(f"   [Filtro Omitió] '{job['title']}' por coincidir con palabra excluida: '{exc}'")
            return False

    # 2. Exigir explícitamente etiquetas de nivel inicial / aprendizaje si la regla lo requiere
    if rule.get("require_entry_level_only", False):
        entry_indicators = [
            "junior", "graduate", "trainee", "intern", "internship",
            "cadet", "apprentice", "entry level", "entry-level",
            "beginner", "assistant"
        ]
        has_entry = any(ind in title for ind in entry_indicators)
        if not has_entry:
            print(f"   [Filtro Omitió] '{job['title']}' por no ser un puesto inicial etiquetado (Junior/Graduate/Trainee/Intern).")
            return False

    # 3. Verificar que pertenezca al dominio (electronics, embedded, firmware, software, pcb, etc.)
    if require_domain:
        matched = any(dom in title or dom in company for dom in require_domain)
        if not matched:
            print(f"   [Filtro Omitió] '{job['title']}' por no contener palabras clave del dominio técnico.")
            return False

    return True

# ── Ciclo de escaneo ──────────────────────────────────────────────────────────

def run_scan_cycle(config):
    seen_path    = os.path.join(DATA_DIR, "seen_jobs.json")
    jobs_db_path = os.path.join(DATA_DIR, "jobs_db.json")

    seen_jobs  = load_json(seen_path, default={})
    jobs_db    = load_json(jobs_db_path, default={})
    telegram   = config.get("telegram", {})
    max_res    = config.get("polling", {}).get("max_results_per_search", 10)
    new_found  = 0

    for rule in config.get("search_rules", []):
        if not rule.get("enabled", True):
            continue
        location        = rule.get("location", "Australia")
        platforms       = rule.get("platforms", ["seek", "linkedin"])
        max_age_minutes = rule.get("max_age_minutes", 30)

        for kw in rule.get("keywords", []):
            print(f"\n🔍 '{kw}' en '{location}' (Máx. {max_age_minutes} min)...")
            found = []
            if "seek" in platforms:
                found.extend(fetch_seek_jobs(kw, location, max_results=max_res, max_age_minutes=max_age_minutes))
            if "linkedin" in platforms:
                found.extend(fetch_linkedin_jobs(kw, location, max_results=max_res, max_age_minutes=max_age_minutes))
            print(f"   → {len(found)} ofertas recientes encontradas.")

            for job in found:
                job_id = job["id"]
                if job_id in seen_jobs:
                    continue

                # Filtrar puestos irrelevantes (Senior, Pharma, fuera de rubro)
                if not is_job_relevant_for_rule(job, rule):
                    # Guardar como visto para no re-evaluarlo constantemente
                    seen_jobs[job_id] = {"title": job["title"], "company": job["company"],
                                         "url": job["url"], "ts": time.time(), "filtered": True}
                    save_json(seen_path, seen_jobs)
                    continue

                # Marcar como visto de inmediato
                seen_jobs[job_id] = {"title": job["title"], "company": job["company"],
                                     "url": job["url"], "ts": time.time()}
                save_json(seen_path, seen_jobs)

                jobs_db[job_id] = {**job, "status": "pending",
                                   "mode": rule.get("mode", "professional"),
                                   "creativity": rule.get("creativity_level", 1)}
                save_json(jobs_db_path, jobs_db)
                new_found += 1

                print(f"\n✨ NUEVA OFERTA FILTRADA Y RELEVANTE: {job['title']} @ {job['company']}")
                print(f"   {job['url']}")

                if telegram.get("enabled"):
                    msg_id = telegram_notifier.send_job_alert_interactive(telegram, job, job_id)
                    print(f"   → Alerta enviada a Telegram (msg_id={msg_id})")
                else:
                    print("   → Telegram desactivado. Oferta guardada en data/jobs_db.json")

    print(f"\n[Scan] Ciclo finalizado. {new_found} ofertas nuevas notificadas.")

# ── Loop de interacción Telegram ──────────────────────────────────────────────

def process_telegram_callbacks(config, offset):
    telegram  = config.get("telegram", {})
    if not telegram.get("enabled"):
        return offset

    bot_token  = telegram.get("bot_token")
    chat_id    = telegram.get("chat_id")
    jobs_db_path = os.path.join(DATA_DIR, "jobs_db.json")

    updates, new_offset = telegram_notifier.get_telegram_updates(bot_token, offset)
    if not updates:
        return new_offset

    jobs_db = load_json(jobs_db_path, default={})

    for update in updates:
        cb = update.get("callback_query")
        if not cb:
            continue

        cb_id    = cb.get("id")
        cb_data  = cb.get("data", "")
        msg_id   = cb.get("message", {}).get("message_id")

        if ":" not in cb_data:
            continue

        action, job_key = cb_data.split(":", 1)
        job_info = jobs_db.get(job_key)

        if not job_info:
            telegram_notifier.answer_callback_query(bot_token, cb_id, "Oferta no encontrada en caché.")
            continue

        if action == "ignore":
            telegram_notifier.answer_callback_query(bot_token, cb_id, "Oferta descartada.")
            telegram_notifier.edit_telegram_message(
                bot_token, chat_id, msg_id,
                f"❌ <b>Descartada:</b> {job_info['title']} en {job_info['company']}"
            )
            jobs_db[job_key]["status"] = "ignored"
            save_json(jobs_db_path, jobs_db)
            continue

        mode  = "professional" if action == "pro" else "survival"
        label = "Professional 💼" if mode == "professional" else "Survival 🛠️"

        telegram_notifier.answer_callback_query(bot_token, cb_id, f"Iniciando {label}...")
        telegram_notifier.edit_telegram_message(
            bot_token, chat_id, msg_id,
            f"⏳ <b>Generando CV {label}...</b>\n\n"
            f"📌 <b>{job_info['title']}</b> en <b>{job_info['company']}</b>\n"
            f"<i>Esto puede tardar ~30 seg con la IA...</i>"
        )

        # ── Llamar a main.py como subproceso ─────────────────────────────────
        creativity = str(job_info.get("creativity", 1))
        cmd = [
            sys.executable, MAIN_PY,
            job_info["url"],
            f"--{mode}",
            "--creativity", creativity,
            "--notify"
        ]
        print(f"\n[Bot] Ejecutando: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            job_url = job_info.get("url", "")
            link_html = f"🔗 <a href='{job_url}'>Ir a la oferta de empleo</a>\n\n" if job_url else ""
            telegram_notifier.edit_telegram_message(
                bot_token, chat_id, msg_id,
                f"✅ <b>¡PROCESADO CON ÉXITO! ({label})</b>\n\n"
                f"📌 <b>{job_info['title']}</b> en <b>{job_info['company']}</b>\n"
                f"{link_html}"
                f"📄 Documentos enviados a continuación."
            )
            jobs_db[job_key]["status"] = "completed"
        else:
            err = result.stderr[-300:] if result.stderr else "desconocido"
            telegram_notifier.edit_telegram_message(
                bot_token, chat_id, msg_id,
                f"⚠️ <b>Error generando documentos para:</b>\n{job_info['title']}\n\n"
                f"<code>{err}</code>"
            )
            print(f"[Bot] Error en main.py:\n{result.stderr}")

        save_json(jobs_db_path, jobs_db)

    return new_offset

# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    print("═" * 52)
    print("  JOB WATCHER — Monitoreo Interactivo vía Telegram")
    print("═" * 52)

    run_once = "--once" in sys.argv or "-o" in sys.argv
    config   = load_json(os.path.join(DATA_DIR, "search_config.json"))
    interval = config.get("polling", {}).get("interval_seconds", 300)

    if run_once:
        print("[Watcher] Modo --once: ejecutando 1 ciclo de escaneo...\n")
        run_scan_cycle(config)
        return

    print(f"[Watcher] Monitoreo activo. Escaneo cada {interval}s (~{interval//60} min).")
    print("Presioná Ctrl+C para detener.\n")

    tg_offset   = 0
    last_scan   = 0

    try:
        while True:
            now = time.time()
            if now - last_scan >= interval:
                run_scan_cycle(config)
                last_scan = time.time()

            # Escuchar clics de botones de Telegram cada 3 segundos
            tg_offset = process_telegram_callbacks(config, tg_offset)
            time.sleep(3)

    except KeyboardInterrupt:
        print("\n[Watcher] Detenido por el usuario.")


if __name__ == "__main__":
    main()
