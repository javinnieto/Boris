# Job Auto-App 🚀

Sistema automatizado de búsqueda de empleo, personalización de CV y Cover Letter con IA (Gemini), y notificaciones en tiempo real via Telegram.

---

## Estructura del Proyecto

```
job_auto_app/
│
├── main.py               ← Punto de entrada principal (interactivo o CLI)
├── job_watcher.py        ← Daemon de monitoreo de portales + integración Telegram
├── requirements.txt
├── README.md
│
├── core/                 ← Módulos de lógica de negocio
│   ├── scraper.py        ← Extrae datos de ofertas (Seek, LinkedIn, Jora, etc.)
│   ├── ai_generator.py   ← Genera Cover Letter, CV adaptado y DM via Gemini
│   ├── prompts.py        ← Todos los prompts de IA
│   ├── doc_builder.py    ← Construye .docx y convierte a PDF
│   └── tracker.py        ← Registra postulaciones en Excel / Google Sheets
│
├── bot/                  ← Módulos de integración con Telegram
│   └── telegram_notifier.py  ← API de Telegram: mensajes, botones, archivos
│
├── templates/            ← Plantillas base del CV (no modificar manualmente)
│   ├── base_resume.docx
│   ├── base_resume.txt
│   ├── base_resume_survival.docx
│   └── base_resume_survival.txt
│
├── data/                 ← Datos persistentes en tiempo de ejecución
│   ├── search_config.json   ← ⚙️  Configurar aquí: keywords, ubicación, Telegram
│   ├── seen_jobs.json       ← Cache de ofertas ya procesadas (auto-generado)
│   ├── jobs_db.json         ← BD de ofertas pendientes/completadas (auto-generado)
│   └── Aplicaciones.xlsx    ← Historial de postulaciones
│
├── output/               ← CVs y Cover Letters generados
│   ├── professional/     ← Modo ingeniería/proyectos
│   ├── survival/         ← Modo técnico/mantenimiento
│   └── backup/           ← Archivos históricos
│
├── scripts/              ← Herramientas de diagnóstico
│   ├── test_telegram.py  ← Verifica permisos y botones del bot
│   └── test_search.py    ← Verifica scraping de Seek y LinkedIn
│
└── venv/                 ← Entorno virtual Python
```

---

## Configuración Inicial

### 1. Variables de entorno
```bash
export GEMINI_API_KEY="tu_clave_de_gemini"
# Opcional:
export GOOGLE_SHEET_WEBAPP_URL="tu_url_de_google_apps_script"
```

### 2. Configurar búsquedas y Telegram Bot
Editá `data/search_config.json`:
```json
{
  "telegram": {
    "enabled": true,
    "bot_token": "TU_BOT_TOKEN",
    "chat_id": "TU_CHAT_ID",
    "send_documents": true
  },
  "search_rules": [
    {
      "name": "Ingeniería",
      "enabled": true,
      "mode": "professional",
      "creativity_level": 1,
      "keywords": ["Mechanical Engineer", "Project Engineer"],
      "location": "Melbourne VIC",
      "platforms": ["seek", "linkedin"]
    }
  ],
  "polling": { "interval_seconds": 300 }
}
```

### 3. Crear el Bot de Telegram (1 minuto)
1. En Telegram, buscá **@BotFather** → `/newbot` → copiá el token.
2. Buscá tu nuevo bot → tocá **INICIAR** (para darle permiso de escritura).
3. Buscá **@userinfobot** → enviá cualquier mensaje → copiá tu `Id`.
4. Pegá ambos valores en `data/search_config.json`.

---

## Uso

### Aplicar a una oferta manualmente (interactivo)
```bash
source venv/bin/activate
python main.py
```

### Aplicar a una oferta por CLI (no-interactivo)
```bash
python main.py "https://www.seek.com.au/job/12345" --pro --creativity 1
python main.py "https://au.linkedin.com/jobs/view/..." --survival
```

### Verificar que el bot de Telegram funciona
```bash
python scripts/test_telegram.py
```

### Lanzar el monitor de empleos en segundo plano
```bash
python job_watcher.py
```
El demonio escaneará Seek y LinkedIn cada 5 minutos.  
Cuando encuentre una oferta nueva, te mandará una alerta a Telegram con los botones:
- **💼 Generar CV Pro** → ejecuta `main.py --pro --notify`
- **🛠️ Generar CV Survival** → ejecuta `main.py --survival --notify`
- **❌ Ignorar** → descarta la oferta
