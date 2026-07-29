import pandas as pd
import os
from datetime import datetime
import requests
import json


def log_application(company, job_title, url, tracker_file=None):
    """
    Registra una postulación en Excel local y opcionalmente en Google Sheets.
    tracker_file: ruta absoluta al archivo Excel. Si es None, usa data/Aplicaciones.xlsx
                  relativo a la raíz del proyecto.
    """
    print("Registrando aplicación...")

    if tracker_file is None:
        # Resolver ruta por defecto: data/ relativo a la raíz del proyecto
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        tracker_file = os.path.join(root, "data", "Aplicaciones.xlsx")

    fecha_actual  = datetime.now().strftime("%Y-%m-%d")
    estado_inicial = "Pendiente"
    clean_url     = str(url).strip()

    # 1. Intentar registrar en Google Sheets si la URL del Webapp está configurada
    webapp_url = os.environ.get("GOOGLE_SHEET_WEBAPP_URL")
    if not webapp_url:
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(root_dir, "data", "search_config.json")
        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    webapp_url = cfg.get("google_sheet_webapp_url")
        except Exception:
            pass

    if webapp_url and webapp_url != "YOUR_GOOGLE_SHEET_WEBAPP_URL":
        print("Enviando datos a tu Google Sheet en la nube...")
        payload = {
            "fecha":   fecha_actual,
            "empresa": company,
            "titulo":  job_title,
            "link":    clean_url,
            "estado":  estado_inicial
        }
        try:
            response = requests.post(
                webapp_url,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    print("¡Registro exitoso en Google Sheets!")
                    return
                elif result.get("status") == "duplicate":
                    print("ℹ️ Esta oferta ya estaba registrada previamente en Google Sheets.")
                    return
                else:
                    print(f"[!] Google Sheets: respuesta inesperada: {result.get('message')}. Guardando en Excel local...")
            else:
                print(f"[!] Google Sheets HTTP {response.status_code}. Guardando en Excel local...")
        except Exception as e:
            print(f"[!] No se pudo conectar con Google Sheets ({e}). Guardando en Excel local...")

    # 2. Fallback a Excel local (con control de duplicados por URL)
    print(f"Registrando en el archivo Excel local: {tracker_file}")
    new_data = {
        "Fecha":            [fecha_actual],
        "Empresa":          [company],
        "Título del Puesto": [job_title],
        "Link":             [clean_url],
        "Estado":           [estado_inicial],
    }
    df_new = pd.DataFrame(new_data)

    if os.path.exists(tracker_file):
        try:
            df_existing = pd.read_excel(tracker_file)
            if "Link" in df_existing.columns and clean_url in df_existing["Link"].astype(str).values:
                print("ℹ️ Esta oferta ya estaba registrada en el archivo Excel local.")
                return
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        except Exception as e:
            print(f"Error leyendo el Excel existente: {e}. Se creará uno nuevo.")
            df_combined = df_new
    else:
        df_combined = df_new

    try:
        df_combined.to_excel(tracker_file, index=False)
        print(f"Registro exitoso local en {os.path.basename(tracker_file)}")
    except Exception as e:
        print(f"Error al guardar en Excel local: {e}")
