"""
main.py — Punto de entrada de Job Auto-App para Javier Nieto.

Uso interactivo (terminal):
    python main.py

Uso CLI no-interactivo (llamado por el bot de Telegram):
    python main.py <URL> --pro [--creativity 1]
    python main.py <URL> --survival [--creativity 2]

Flags disponibles:
    --pro / -p         Modo professional (ingeniería, proyectos)
    --survival / -s    Modo survival (técnico, mantenimiento, depósito)
    --creativity N     Nivel de creatividad 1/2/3 (por defecto: 1 en modo CLI)
    --notify           Si está presente, envía los docs finales por Telegram
"""

import sys
import os
import json

# ── Resolver rutas relativas al proyecto (root del proyecto = directorio de este archivo)
ROOT = os.path.dirname(os.path.abspath(__file__))
CORE_DIR = os.path.join(ROOT, "core")
TEMPLATES_DIR = os.path.join(ROOT, "templates")
DATA_DIR = os.path.join(ROOT, "data")
OUTPUT_DIR = os.path.join(ROOT, "output")

# Agregar core/ al path para importar los módulos sin instalar como paquete
sys.path.insert(0, CORE_DIR)


def load_base_resume(filename):
    path = os.path.join(TEMPLATES_DIR, filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: No se encontró la plantilla '{path}'.")
        return None


def load_telegram_config():
    config_path = os.path.join(DATA_DIR, "search_config.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f).get("telegram", {})
    except Exception:
        return {}


def main():
    print("=== Job Auto-App para Javier ===")

    # ── Parseo de argumentos CLI ───────────────────────────────────────────────
    mode = None
    creativity_level = None
    notify_telegram = False
    args = sys.argv[1:]
    url_args = []

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ("--survival", "-s", "survival"):
            mode = "survival"
        elif arg in ("--pro", "-p", "pro", "professional"):
            mode = "professional"
        elif arg in ("--creativity", "-c") and i + 1 < len(args):
            try:
                creativity_level = max(1, min(3, int(args[i + 1])))
            except ValueError:
                creativity_level = 1
            i += 1
        elif arg == "--notify":
            notify_telegram = True
        else:
            url_args.append(arg)
        i += 1

    is_cli_run = bool(url_args)

    # ── URL ───────────────────────────────────────────────────────────────────
    if url_args:
        url = url_args[0].strip().replace("\\", "")
    else:
        url = input("Ingresa la URL del trabajo (Seek, LinkedIn, Jora, Indeed, etc.): ").strip()

    if not url:
        print("URL vacía. Saliendo...")
        sys.exit(1)

    print(f"URL a procesar: {url}")

    # ── Modo ──────────────────────────────────────────────────────────────────
    if not mode:
        if is_cli_run:
            mode = "professional"
        else:
            print("\nSelecciona el tipo de trabajo:")
            print("  1. Profesional / Ingeniería (Por defecto)")
            print("  2. Supervivencia (Técnico, Mantenimiento, Depósito, Limpieza, Farm)")
            opcion = input("Opción [1/2]: ").strip()
            mode = "survival" if opcion == "2" else "professional"

    print(f"\n[Modo Activo: {mode.upper()}]")

    # ── Creatividad ───────────────────────────────────────────────────────────
    if creativity_level is None:
        if is_cli_run:
            creativity_level = 1
        else:
            print("\nNivel de creatividad para el CV:")
            print("  1. Sutil y discreto – mínimos cambios, casi idéntico al original (Por defecto)")
            print("  2. Balanceado – reformula el perfil y adapta entre 3-4 viñetas de forma orgánica")
            print("  3. Estratégico – libertad total para presentar el perfil perfecto para la oferta")
            try:
                creativity_level = int(input("Creatividad [1/2/3]: ").strip())
                if creativity_level not in (1, 2, 3):
                    creativity_level = 1
            except ValueError:
                creativity_level = 1

    print(f"[Creatividad: Nivel {creativity_level}]")

    # ── Rutas según modo ──────────────────────────────────────────────────────
    if mode == "survival":
        base_resume_txt  = "base_resume_survival.txt"
        base_resume_docx = os.path.join(TEMPLATES_DIR, "base_resume_survival.docx")
        output_base_dir  = os.path.join(OUTPUT_DIR, "survival")
    else:
        base_resume_txt  = "base_resume.txt"
        base_resume_docx = os.path.join(TEMPLATES_DIR, "base_resume.docx")
        output_base_dir  = os.path.join(OUTPUT_DIR, "professional")

    # ── Importar módulos desde core/ ──────────────────────────────────────────
    import scraper
    import ai_generator
    import doc_builder
    import tracker

    # ── 1. Scraping ───────────────────────────────────────────────────────────
    job_data = scraper.get_job_data(url)
    if not job_data:
        print("No se pudo obtener la información del trabajo.")
        sys.exit(1)

    print(f"\nTrabajo encontrado: {job_data['title']} en {job_data['company']}")

    # ── 2. Detectar reclutador ────────────────────────────────────────────────
    contact_person = ai_generator.find_recruiter_name(
        job_data["raw_page_text"] + " " + job_data["description"]
    )
    print(f"Contacto/Reclutador detectado por IA: {contact_person}")

    # ── 3. Cargar CV base ─────────────────────────────────────────────────────
    base_resume = load_base_resume(base_resume_txt)
    if not base_resume:
        sys.exit(1)

    # ── 4. Generar contenido con Gemini ───────────────────────────────────────
    print("\nGenerando Cover Letter con IA...")
    cover_letter = ai_generator.generate_cover_letter(
        base_resume, job_data["description"], contact_person, mode=mode
    )

    print("Generando CV personalizado con IA...")
    tailored_data = ai_generator.tailor_resume(
        base_resume, job_data["description"],
        mode=mode, creativity_level=creativity_level, template_path=base_resume_docx
    )

    print("Generando Mensaje Directo (DM) con IA...")
    direct_message = ai_generator.generate_direct_message(
        base_resume, job_data["description"], job_data["title"],
        job_data["company"], contact_person, mode=mode
    )

    if not cover_letter or cover_letter.startswith("Error"):
        print("Error generando la Cover Letter.")
        sys.exit(1)
    if not tailored_data:
        print("Error generando la adaptación del CV.")
        sys.exit(1)

    # ── 5. Estructura de carpetas de salida ───────────────────────────────────
    company_clean   = "".join(c if c.isalnum() else "_" for c in job_data["company"])
    job_title_clean = "".join(c if c.isalnum() else "_" for c in job_data["title"])

    output_folder = os.path.join(output_base_dir, company_clean, job_title_clean)
    os.makedirs(output_folder, exist_ok=True)

    # ── 6. Nombres de archivo ─────────────────────────────────────────────────
    cover_path  = os.path.join(output_folder, f"cover_JavierNieto_{company_clean}.docx")
    resume_path = os.path.join(output_folder, f"resume_JavierNieto_{company_clean}.docx")
    dm_path     = os.path.join(output_folder, f"dm_JavierNieto_{company_clean}.txt")

    # ── 7. Construir documentos Word ──────────────────────────────────────────
    print("\nGenerando documentos basados en tus plantillas Word...")
    cover_template = os.path.join(TEMPLATES_DIR, "base_cover_letter.docx")
    doc_builder.build_cover_letter_from_template(cover_letter, cover_path, cover_template)
    doc_builder.build_resume_from_template(tailored_data, resume_path, base_resume_docx)

    with open(dm_path, "w", encoding="utf-8") as f:
        f.write(direct_message)
    print(f"Mensaje Directo guardado en: {dm_path}")

    # ── 8. Convertir a PDF ────────────────────────────────────────────────────
    doc_builder.convert_to_pdf(cover_path, output_folder)
    doc_builder.convert_to_pdf(resume_path, output_folder)

    # ── 9. Registrar en Excel / Google Sheets ─────────────────────────────────
    tracker_file = os.path.join(DATA_DIR, "Aplicaciones.xlsx")
    tracker.log_application(job_data["company"], job_data["title"], job_data["url"],
                            tracker_file=tracker_file)

    # ── 10. Notificación Telegram si se solicitó ──────────────────────────────
    if notify_telegram:
        sys.path.insert(0, os.path.join(ROOT, "bot"))
        import telegram_notifier
        telegram_config = load_telegram_config()
        if telegram_config.get("enabled"):
            telegram_notifier.notify_job_completed(
                telegram_config, job_data, output_folder, direct_message
            )

    # ── 11. Output final ──────────────────────────────────────────────────────
    print(f"\n=== ¡Proceso completado! ===")
    print(f"Archivos en: {output_folder}")
    print("\n" + "─" * 50)
    print("📩 MENSAJE DIRECTO (DM):")
    print("─" * 50)
    print(direct_message)
    print("─" * 50 + "\n")


if __name__ == "__main__":
    main()
