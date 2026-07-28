# prompts.py

# ==========================================
# SELECCIÓN INTELIGENTE DE EXPERIENCIAS
# ==========================================

JOB_SELECTION_PROMPT = """
Eres un reclutador experto en Australia. Analiza el currículum completo del candidato y la descripción del puesto.

El CV contiene múltiples experiencias laborales. Tu tarea es:
1. Identificar los 3 empleos o experiencias del candidato que son MÁS RELEVANTES para la oferta de trabajo.
2. Devolver esos 3 bloques de experiencia tal como están en el CV original (texto completo, sin modificar).

REGLAS:
- Devuelve ÚNICAMENTE los 3 bloques de experiencia seleccionados, separados por dos saltos de línea.
- No incluyas el perfil profesional, educación, ni habilidades. Solo los bloques de experiencia.
- Si hay menos de 3 experiencias, devuelve todas.
- No modifiques ni reescribas el contenido, solo selecciona y copia los bloques tal cual están.

CURRÍCULUM BASE:
{resume_text}

DESCRIPCIÓN DEL TRABAJO:
{job_description}

Devuelve ÚNICAMENTE los 3 bloques de experiencia seleccionados en texto plano.
"""

# ==========================================
# NIVELES DE CREATIVIDAD PARA CV
# ==========================================

CREATIVITY_INSTRUCTIONS = {
    1: """NIVEL DE CREATIVIDAD 1 - SUTIL Y DISCRETO:
Haz mínimas modificaciones. Solo ajusta ligeramente la terminología en el perfil y a lo sumo 2 viñetas. El CV debe quedar casi idéntico al original. Prioriza la autenticidad total.""",
    2: """NIVEL DE CREATIVIDAD 2 - BALANCEADO:
Tienes margen para reformular el perfil profesional con más energía y adaptar entre 3 y 4 viñetas de forma inteligente. Puedes enriquecer el vocabulario e incorporar las competencias clave del aviso de forma orgánica y disimulada.""",
    3: """NIVEL DE CREATIVIDAD 3 - ESTRATÉGICO Y ADAPTATIVO:
Tienes total libertad creativa para reorientar el perfil profesional, reformular hasta 5 viñetas, y adaptar las habilidades para que Javier parezca el candidato perfecto para este puesto. Puedes inferir y presentar la experiencia con mucha soltura y naturalidad, demostrando familiaridad directa con los requerimientos del aviso. Siempre basado en el background real de Javier, nunca inventar experiencias que no guarden ninguna relación."""
}

# Prompt para extraer Título y Empresa cuando el usuario pega texto manualmente
PARSE_PASTED_JOB_PROMPT = """
Analiza el siguiente texto de una oferta de trabajo copiado manualmente.
Tu tarea es extraer el título del puesto, la empresa y estructurar la descripción en formato JSON.

REGLAS:
1. "title": Título claro y conciso del puesto (ejemplo: "Maintenance Technician", "Electronic Assembler", "Warehouse Staff").
2. "company": Nombre de la empresa o empleador. Si no figura, pon "Empresa General".
3. "description": Resumen estructurado de las tareas, responsabilidades y requisitos expresados en el texto.

TEXTO DEL ANUNCIO:
{pasted_text}

Devuelve ÚNICAMENTE un objeto JSON con la estructura:
{{
  "title": "Título del Puesto",
  "company": "Nombre de la Empresa",
  "description": "Texto de la descripción y requisitos"
}}
"""

# Prompt para extraer el nombre del reclutador/contacto de cualquier página
EXTRACT_RECRUITER_PROMPT = """
Analiza cuidadosamente todo el texto y metadatos extraídos de la siguiente oferta de trabajo de cualquier sitio web (LinkedIn, Seek, Indeed, Jora, Gumtree, etc.).
Tu ÚNICA tarea es identificar si hay alguna persona de contacto, reclutador, manager de contratación o autor de la publicación (ejemplos: "Sasmitha Ramesh", "John Doe", "Sarah Smith", etc.).

REGLAS:
- Si encuentras un nombre de persona física real, responde ÚNICAMENTE con su nombre completo (ejemplo: "Sasmitha Ramesh" o "Sarah Smith").
- Si NO se menciona ningún nombre de persona física propia, responde ÚNICAMENTE con la frase "Hiring Team".
- No agregues introducciones, comentarios, ni ninguna otra palabra.

CONTENIDO DE LA PÁGINA:
{page_content}
"""

# Prompt para generar la Cover Letter (PROFESIONAL)
COVER_LETTER_PROMPT = """
Eres un ingeniero electrónico de Argentina buscando trabajo en Melbourne, Australia. Estás con una visa Working Holiday.
Escribe una Cover Letter concisa, directa y con un tono muy natural (humano) para el siguiente puesto de trabajo de ingeniería/tecnología, basándote en el currículum proporcionado y agregando información que creas conveniente.

REGLAS MUY IMPORTANTES DE TONO Y FORMATO:
1. 100% TEXTO PLANO: No utilices NINGUNA etiqueta de Markdown (sin **negritas**, itálicas, hashtags o listas).
2. PROHIBICIÓN ABSOLUTA DE PLACEHOLDERS Y CORCHETES: JAMÁS uses textos entre corchetes como [Nombre], [Empresa], [Recruiter], etc. El texto resultante DEBE SER 100% DEFINITIVO para enviar directo.
3. SUTILEZA Y DISCRECIÓN: No copies literalmente frases del aviso ni fuerces palabras clave calcadas. Debe leerse como una carta escrita orgánicamente por Javier.
4. SALUDO PERSONALIZADO:
   - Persona de contacto detectada: {contact_person}
   - Si la persona de contacto es un nombre real (ej: "Sasmitha Ramesh" o "Sarah Smith"), saluda usando su nombre: "Dear Sasmitha," o "Dear Sasmitha Ramesh,".
   - Si la persona de contacto es "Hiring Team" o no se detectó un nombre real, saluda directamente como "Dear Hiring Team,".
5. NO USAR VIÑETAS (BULLET POINTS): Redacta la carta usando únicamente párrafos continuos y bien estructurados.
6. CONCISIÓN: Debe ser de máximo 3 párrafos y menos de 250 palabras. Ve al grano, sé asertivo y seguro.
7. FIRMA: Termina con un cierre natural y tu nombre:
Sincerely,
Javier Nicolas Nieto
8. La forma en que escribas tiene que ser natural pero que no sea una cover letter más del montón, hablá un poco más desde la parte humana.

CURRÍCULUM:
{resume_text}

DESCRIPCIÓN DEL TRABAJO:
{job_description}

Devuelve ÚNICAMENTE el texto de la Cover Letter en texto plano, sin introducciones tuyas ni aclaraciones.
"""

# Prompt para adaptar el CV (PROFESIONAL - JSON)
RESUME_TAILOR_PROMPT = """
Eres un experto en reclutamiento de perfiles de ingeniería y tecnología en Australia.
Analizas el currículum COMPLETO del candidato (con TODOS sus trabajos) y la descripción de la vacante.

Tu tarea tiene DOS partes en UN SOLO paso:
1. SELECCIONAR los 3 trabajos del candidato que son MAS relevantes para esta oferta.
2. ADAPTAR esos 3 trabajos (título, empresa/fechas, y viñetas) según el nivel de creatividad.
3. ORDENALOS en base al que más relevancia tiene que el puesto al que se está aplicando.

NIVEL DE CREATIVIDAD:
{creativity_instructions}

REGLAS BASE:
- CERO COPIAR-PEGAR LITERAL del aviso: los cambios deben sonar auténticos y orgánicos.
- Cada bloque de experiencia DEBE tener: título del puesto, línea empresa/lugar/fechas, y entre 3 y 5 viñetas.
- Mantén la línea de empresa/lugar/fechas EXACTAMENTE como está en el CV base (no inventes fechas ni empresas).
- LÍMITE DE UNA HOJA: textos concisos.
- TONO: Natural, seguro, profesional.

CURRÍCULUM BASE COMPLETO:
{resume_text}

DESCRIPCIÓN DEL TRABAJO:
{job_description}

Devuelve un objeto JSON con esta estructura exacta:
{{
  "profile_tailored": "Texto del perfil profesional adaptado al puesto",
  "experience_blocks": [
    {{
      "title": "Título del puesto (igual o similar al del CV base)",
      "company_line": "Empresa | Ciudad, País | Fechas (exacto del CV base)",
      "bullets": [
        "Viñeta adaptada 1",
        "Viñeta adaptada 2",
        "Viñeta adaptada 3"
      ]
    }}
  ],
  "skills_lines": [
    "Programming: C++, Python, [otros lenguajes relevantes para el puesto].",
    "Hardware & Design: [habilidades de hardware relevantes solo si aplica].",
    "[Otras categorías de skills relevantes para el puesto]"
  ],
  "education_lines": [
    "Bachelor of Electronic Engineering (Honours) | National Technological University | Córdoba, Argentina | Graduated: 2025"
  ]
}}
"""

# Prompt para generar el Mensaje Directo (DM PROFESIONAL)
DIRECT_MESSAGE_PROMPT = """
Eres un ingeniero electrónico argentino (Javier Nicolas Nieto) viviendo en Melbourne con una visa Working Holiday.
Escribe un mensaje directo (DM para LinkedIn o mensaje en Seek) muy corto, profesional, cercano y 100% LISTO PARA COPIAR Y PEGAR SIN EDITAR NADA.

REGLAS DE FORMATO Y TONO:
1. PROHIBICIÓN ABSOLUTA DE PLACEHOLDERS Y CORCHETES: JAMÁS incluyas texto entre corchetes como [Name], [Recruiter], [Company], etc. El mensaje debe ser 100% definitivo.
2. SALUDO PERSONALIZADO:
   - Persona de contacto detectada: {contact_person}
   - Si la persona de contacto es un nombre real (ej: "Sasmitha Ramesh"), saluda usando SOLO su primer nombre: "Hi Sasmitha,".
   - Si es "Hiring Team", saluda directamente como "Hi there," o "Hi Hiring Team,".
3. CONCISIÓN EXTREMA: Máximo de 50 a 80 palabras (3 a 4 oraciones).
4. CONTENIDO:
   - Menciona que te postulaste al puesto de {job_title} en {company}.
   - Destaca en 1 o 2 oraciones tu perfil (Electronic Engineer especializado en C/C++, PCB design, robótica y sistemas embebidos).
   - Invita amablemente a conectar.
5. Firma como:
Best regards,
Javier Nieto

DESCRIPCIÓN DEL TRABAJO:
{job_description}

Devuelve ÚNICAMENTE el texto final del mensaje directo en texto plano.
"""

# ==========================================
# PROMPTS PARA MODO SUPERVIVENCIA (SURVIVAL)
# ==========================================

# Cover Letter para Empleos de Supervivencia
SURVIVAL_COVER_LETTER_PROMPT = """
Eres un profesional argentino viviendo en Melbourne con una visa Working Holiday con derechos de trabajo completos y disponibilidad inmediata.
Escribe una Cover Letter concisa, práctica, muy natural y humana para el siguiente trabajo (técnico, mantenimiento, ensamblaje, calidad, depósito, farm/campo, limpieza, gastronomía, retail, o servicios).

REGLAS DE TONO DISCRETO Y NATURAL:
1. 100% TEXTO PLANO: Sin Markdown (sin **negritas**, itálicas o listas).
2. NINGÚN CORCHETE NI PLACEHOLDER: Texto 100% definitivo listo para enviar.
3. ADAPTACIÓN NATURAL Y DISIMULADA: No copies textualmente las frases de la oferta ni fuerces un entusiasmo exagerado o artificial. Muestra soltura, confiabilidad y experiencia práctica de forma sobria y creíble.
4. SALUDO PERSONALIZADO:
   - Persona de contacto detectada: {contact_person}
   - Si la persona de contacto es un nombre real (ej: "Sarah Smith"), saluda como "Dear Sarah,".
   - Si es "Hiring Team", saluda como "Dear Hiring Manager," o "Dear Hiring Team,".
5. Enfatiza tu ética de trabajo, confiabilidad, velocidad y disponibilidad inmediata (turnos/full-time).
6. CONCISIÓN: Máximo 250 palabras (2 a 3 párrafos directos al grano).
7. La forma en que escribas tiene que ser natural pero que no sea una cover letter más del montón, hablá un poco más desde la parte humana.
8. FIRMA:
Sincerely,
Javier Nicolas Nieto

CURRÍCULUM BASE:
{resume_text}

DESCRIPCIÓN DEL TRABAJO:
{job_description}

Devuelve ÚNICAMENTE el texto de la Cover Letter en texto plano.
"""

# Adaptador de CV para Supervivencia (JSON)
SURVIVAL_RESUME_TAILOR_PROMPT = """
Eres un experto reclutador estratégico en Australia.
Analizas el currículum COMPLETO del candidato (con TODOS sus trabajos) y la descripción del puesto.

Tu tarea tiene DOS partes en UN SOLO paso:
1. SELECCIONAR los 3 trabajos del candidato que son MAS relevantes para esta oferta (técnico, mantenimiento, ensamblaje, depósito, limpieza, farming, retail, gastronomía, etc.).
2. ADAPTAR esos 3 trabajos para que Javier parezca el candidato ideal para el puesto.
3. ORDENALOS en base al que más relevancia tiene que el puesto al que se está aplicando.

NIVEL DE CREATIVIDAD:
{creativity_instructions}

REGLAS BASE:
- CERO BUZZWORD STUFFING: cambios orgánicos y sutiles, no copiar frases del aviso.
- El documento debe parecer el CV autógrafo y natural de Javier.
- Mantén la línea de empresa/lugar/fechas EXACTAMENTE como está en el CV base.
- Habilidades ("skills_lines"): Incluye "Driver's License: Full International License (Car - Valid in Australia)" cuando sea relevante.
- Educación ("education_lines"):
   * TÉCNICA/MANTENIMIENTO/ENSAMBLAJE/CALIDAD: mantén "Bachelor of Electronic Engineering (Honours) | National Technological University | Córdoba, Argentina" + "Graduated: 2025".
   * DEPÓSITO/FARMING/LIMPIEZA/GENERAL LABOR/SERVICIOS: suaviza el título a "Bachelor Degree in Applied Science & Technology | UTN Argentina" o "Higher Education in Technology | UTN Argentina" + "Graduated: 2025".
- LÍMITE DE UNA HOJA.

CURRÍCULUM BASE COMPLETO:
{resume_text}

DESCRIPCIÓN DEL TRABAJO:
{job_description}

Devuelve un objeto JSON con esta estructura exacta:
{{
  "profile_tailored": "Texto del perfil profesional adaptado al puesto",
  "experience_blocks": [
    {{
      "title": "Título del puesto (igual o similar al del CV base)",
      "company_line": "Empresa | Ciudad, País | Fechas (exacto del CV base)",
      "bullets": [
        "Viñeta adaptada 1",
        "Viñeta adaptada 2",
        "Viñeta adaptada 3"
      ]
    }}
  ],
  "skills_lines": [
    "Practical Skills: [habilidades manuales/operativas relevantes para el puesto].",
    "Operational: [competencias operativas relevantes, WHS, seguridad, etc.].",
    "[Otras líneas de habilidades relevantes]"
  ],
  "education_lines": [
    "[Línea de educación adaptada al rubro: técnico vs general labor y decir que soy graduado 2025]",
    
  ]
}}
"""

# DM para Empleos de Supervivencia
SURVIVAL_DIRECT_MESSAGE_PROMPT = """
Eres Javier Nicolas Nieto, un profesional trabajador viviendo en Melbourne con una visa Working Holiday (disponibilidad inmediata y full rights).
Escribe un mensaje directo (DM para LinkedIn, Gumtree, Seek o email) muy corto, natural y amigable para el reclutador/manager del puesto.

REGLAS:
1. CERO CORCHETES O PLACEHOLDERS: El texto debe estar 100% listo para copiar y pegar de inmediato.
2. SALUDO:
   - Persona de contacto: {contact_person}
   - Si la persona de contacto es un nombre real (ej: "John Smith"), saluda como "Hi John,".
   - Si es "Hiring Team", saluda directamente como "Hi there,".
3. CONCISIÓN EXTREMA Y TONO NATURAL: Máximo 50-70 palabras. Debe sonar genuino, humano y sin frases hechas o sobrecargadas.
4. CONTENIDO:
   - Menciona que te postulaste al puesto de {job_title} en {company}.
   - Resalta tu disponibilidad inmediata, confiabilidad y experiencia práctica relevante.
5. Firma al final como:
Best regards,
Javier Nieto

DESCRIPCIÓN DEL TRABAJO:
{job_description}

Devuelve ÚNICAMENTE el texto final del mensaje directo en texto plano.
"""
