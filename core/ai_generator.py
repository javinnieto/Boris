import os
import prompts
import json
from google import genai
from google.genai import types

def get_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        # Fallback: intentar cargar la clave desde data/search_config.json
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(root_dir, "data", "search_config.json")
        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    api_key = cfg.get("gemini_api_key") or cfg.get("gemini", {}).get("api_key")
        except Exception:
            pass

    if not api_key or api_key in ("YOUR_GEMINI_API_KEY", "YOUR_GEMINI_KEY"):
        print("ERROR: No se encontró GEMINI_API_KEY en las variables de entorno ni en data/search_config.json.")
        print("Configurá tu clave en data/search_config.json bajo 'gemini_api_key': 'TU_CLAVE'")
        return None

    return genai.Client(api_key=api_key)

def get_clean_models(client):
    preferred_models = [
        'gemini-3.5-flash',
        'gemini-flash-latest',
        'gemini-2.5-flash',
        'gemini-2.0-flash',
        'gemini-pro-latest'
    ]
    
    try:
        api_models = []
        for m in client.models.list():
            name = m.name.replace('models/', '') if hasattr(m, 'name') else str(m)
            name_lower = name.lower()
            if any(bad in name_lower for bad in ['tts', 'audio', 'imagen', 'embed', 'computer-use']):
                continue
            api_models.append(name)
            
        final_list = []
        for pref in preferred_models:
            for m in api_models:
                if (pref == m or pref in m) and m not in final_list:
                    final_list.append(m)
                    
        for m in api_models:
            if m not in final_list:
                final_list.append(m)
                
        return final_list if final_list else preferred_models
    except Exception:
        return preferred_models

def call_with_fallback(prompt, response_mime_type=None):
    client = get_client()
    if not client:
        return None
        
    models_to_try = get_clean_models(client)
    
    config = None
    if response_mime_type:
        config = types.GenerateContentConfig(response_mime_type=response_mime_type)
        
    for model_name in models_to_try:
        try:
            print(f"Generando con modelo: {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config
            )
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            err_str = str(e)
            if "RESOURCE_EXHAUSTED" in err_str or "429" in err_str:
                print(f" -> Cuota de {model_name} agotada. Probando siguiente modelo...")
                continue
            elif "NOT_FOUND" in err_str or "404" in err_str or "INVALID_ARGUMENT" in err_str:
                print(f" -> Modelo {model_name} no disponible para texto. Probando siguiente...")
                continue
            else:
                print(f" -> Aviso en {model_name}: {e}. Probando siguiente...")
                continue
                
    print("ERROR: No se pudo completar la solicitud. Espera 1 minuto a que se libere la cuota.")
    return None

def safe_parse_json(text):
    if not text:
        return None
    cleaned = text.strip()
    if "```" in cleaned:
        import re
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', cleaned, re.IGNORECASE)
        if match:
            cleaned = match.group(1).strip()
        else:
            lines = [line for line in cleaned.splitlines() if not line.strip().startswith("```")]
            cleaned = "\n".join(lines).strip()

    start_idx = cleaned.find('{')
    end_idx = cleaned.rfind('}')
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        cleaned = cleaned[start_idx:end_idx+1]

    try:
        return json.loads(cleaned)
    except Exception as e:
        print(f"Error parseando JSON: {e}")
        try:
            import re
            cleaned_fixed = re.sub(r',\s*([}\]])', r'\1', cleaned)
            return json.loads(cleaned_fixed)
        except Exception:
            return None

def parse_pasted_job_text(pasted_text):
    print("Analizando texto pegado con IA para extraer Título, Empresa y Requisitos...")
    prompt = prompts.PARSE_PASTED_JOB_PROMPT.format(pasted_text=pasted_text[:4000])
    result_text = call_with_fallback(prompt, response_mime_type="application/json")
    parsed = safe_parse_json(result_text)
    if parsed and isinstance(parsed, dict):
        return parsed
    return {
        "title": "Puesto de Trabajo",
        "company": "Empresa General",
        "description": pasted_text
    }

def select_relevant_jobs(resume_text, job_description):
    """
    Usa la IA para seleccionar los 3 bloques de experiencia más relevantes del CV
    para el puesto dado. Devuelve el texto de esos 3 bloques para reemplazar la
    sección de experiencia en el resume que se pasa a tailor_resume().
    """
    print("Seleccionando los 3 trabajos más relevantes con IA...")
    prompt = prompts.JOB_SELECTION_PROMPT.format(
        resume_text=resume_text,
        job_description=job_description
    )
    result = call_with_fallback(prompt)
    if result and len(result.strip()) > 50:
        return result.strip()
    # Fallback: devolver el texto tal cual si la IA falla
    return resume_text

def find_recruiter_name(page_content):
    print("Buscando reclutador/contacto de forma inteligente con IA...")
    prompt = prompts.EXTRACT_RECRUITER_PROMPT.format(
        page_content=page_content[:5000]
    )
    result = call_with_fallback(prompt)
    if not result or result.lower() == "hiring team" or "[" in result:
        return "Hiring Team"
    return result.strip()

def generate_cover_letter(resume_text, job_description, contact_person="Hiring Team", mode="professional"):
    print("Generando Cover Letter con IA...")
    prompt_template = prompts.SURVIVAL_COVER_LETTER_PROMPT if mode == "survival" else prompts.COVER_LETTER_PROMPT
    prompt = prompt_template.format(
        resume_text=resume_text,
        job_description=job_description,
        contact_person=contact_person
    )
    result = call_with_fallback(prompt)
    if not result:
        return "Error: No se pudo generar la Cover Letter por límite de cuota temporal."
    return result

def tailor_resume(resume_text, job_description, mode="professional", creativity_level=1, template_path="base_resume.docx"):
    print("Seleccionando los 3 mejores trabajos y adaptando CV con IA...")

    # Instrucciones de creatividad
    creativity_instructions = prompts.CREATIVITY_INSTRUCTIONS.get(creativity_level, prompts.CREATIVITY_INSTRUCTIONS[1])

    prompt_template = prompts.SURVIVAL_RESUME_TAILOR_PROMPT if mode == "survival" else prompts.RESUME_TAILOR_PROMPT
    prompt = prompt_template.format(
        resume_text=resume_text,
        job_description=job_description,
        creativity_instructions=creativity_instructions
    )

    result_text = call_with_fallback(prompt, response_mime_type="application/json")

    if not result_text:
        return {
            "profile_tailored": "Error al adaptar perfil por cuota",
            "experience_blocks": []
        }

    parsed = safe_parse_json(result_text)
    if parsed and isinstance(parsed, dict):
        return parsed
    
    print("Error: No se pudo parsear el JSON de respuesta de la IA.")
    return {
        "profile_tailored": "Error en formato de respuesta",
        "experience_blocks": []
    }

def generate_direct_message(resume_text, job_description, job_title, company, contact_person="Hiring Team", mode="professional"):
    print("Generando Mensaje Directo (DM)...")
    prompt_template = prompts.SURVIVAL_DIRECT_MESSAGE_PROMPT if mode == "survival" else prompts.DIRECT_MESSAGE_PROMPT
    prompt = prompt_template.format(
        job_title=job_title,
        company=company,
        job_description=job_description,
        contact_person=contact_person
    )
    result = call_with_fallback(prompt)
    if not result:
        greeting = f"Hi {contact_person.split()[0]}," if contact_person and contact_person != "Hiring Team" else "Hi there,"
        return f"{greeting}\n\nI recently applied for the {job_title} role at {company} and wanted to express my strong interest. I'd love to connect!\n\nBest regards,\nJavier Nieto"
    return result
