import requests
from bs4 import BeautifulSoup
import json
import re

def parse_json_ld(soup):
    """ Intenta extraer metadatos estructurados (Schema.org JobPosting) del HTML """
    scripts = soup.find_all('script', type='application/ld+json')
    for script in scripts:
        if not script.string:
            continue
        try:
            data = json.loads(script.string)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get('@type') == 'JobPosting':
                        return item
            elif isinstance(data, dict):
                if data.get('@type') == 'JobPosting':
                    return data
                if '@graph' in data and isinstance(data['@graph'], list):
                    for item in data['@graph']:
                        if isinstance(item, dict) and item.get('@type') == 'JobPosting':
                            return item
        except Exception:
            continue
    return None

def fetch_url_content(url):
    """
    Intenta obtener el contenido HTML de cualquier portal de empleo.
    1. Usa requests estándar.
    2. Si devuelve 403 Forbidden o bloqueos anti-bot, usa curl_cffi (Chrome TLS Impersonation).
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200 and len(r.text) > 500:
            return r.text
    except Exception:
        pass
        
    # Intentar bypass con impersonación TLS de Chrome (curl_cffi)
    try:
        from curl_cffi import requests as crequests
        r2 = crequests.get(url, impersonate="chrome120", timeout=12)
        if r2.status_code == 200:
            return r2.text
    except Exception:
        pass
        
    return None

def get_multiline_input(prompt_text):
    """
    Permite pegar bloques gigantes de texto en la terminal sin cortar a los 2 Enters.
    Requiere 4 ENTERS seguidos (o escribir 'FIN' y dar Enter) para finalizar.
    """
    print("\n" + "="*60)
    print(f"📋 {prompt_text}")
    print("="*60)
    print("👉 Pega todo el texto del aviso (Ctrl+V) y presiona ENTER 4 VECES seguidas (o escribe FIN y da Enter):")
    print("------------------------------------------------------------")
    lines = []
    empty_counter = 0
    while True:
        try:
            line = input()
            clean_line = line.strip()
            if clean_line.upper() in ["FIN", "END"]:
                break
            if not clean_line:
                empty_counter += 1
                if empty_counter >= 4:
                    break
            else:
                empty_counter = 0
                lines.append(line)
        except (EOFError, KeyboardInterrupt):
            break
    return "\n".join(lines).strip()

def scrape_seek(url):
    print(f"Buscando en Seek: {url}")
    html_text = fetch_url_content(url)
    if not html_text:
        return handle_manual_paste_fallback(url)

    try:
        soup = BeautifulSoup(html_text, 'html.parser')
        raw_page_text = soup.get_text(separator=' ', strip=True)
        title = None
        company = None
        description = None
        
        json_ld = parse_json_ld(soup)
        if json_ld:
            title = json_ld.get('title')
            org = json_ld.get('hiringOrganization')
            if isinstance(org, dict):
                company = org.get('name')
            elif isinstance(org, str):
                company = org
            description = json_ld.get('description')
            if description:
                desc_soup = BeautifulSoup(description, 'html.parser')
                description = desc_soup.get_text(separator='\n', strip=True)

        if not title:
            t_elem = soup.find(attrs={"data-automation": "job-detail-title"}) or soup.find('h1')
            if t_elem:
                title = t_elem.text.strip()
            else:
                page_title = soup.find('title')
                if page_title:
                    clean_t = page_title.text.split(' Job in ')[0].split(' - ')[0].strip()
                    title = clean_t
                    
        if not company:
            c_elem = (soup.find(attrs={"data-automation": "advertiser-name"}) or 
                      soup.find(attrs={"data-automation": "job-detail-company"}) or
                      soup.find('span', {'data-automation': 'advertiser-name'}))
            if c_elem:
                company = c_elem.text.strip()
            else:
                meta_author = soup.find('meta', {'name': 'author'}) or soup.find('meta', {'property': 'og:site_name'})
                if meta_author and meta_author.get('content'):
                    company = meta_author['content'].strip()

        if not description:
            job_details = (soup.find(attrs={"data-automation": "jobAdDetails"}) or 
                           soup.find(attrs={"data-automation": "job-description"}) or
                           soup.find('div', {'data-automation': 'job-details'}))
            if job_details:
                description = job_details.get_text(separator='\n', strip=True)

        if not title or title == "Título no encontrado" or not company:
            return handle_manual_paste_fallback(url)

        return {
            'title': title,
            'company': company,
            'description': description or "Descripción no disponible",
            'raw_page_text': raw_page_text,
            'url': url
        }
    except Exception as e:
        print(f"Error al procesar Seek: {e}")
        return handle_manual_paste_fallback(url)

def scrape_linkedin(url):
    print(f"Buscando en LinkedIn: {url}")
    html_text = fetch_url_content(url)
    if not html_text:
        return handle_manual_paste_fallback(url)

    try:
        soup = BeautifulSoup(html_text, 'html.parser')
        raw_page_text = soup.get_text(separator=' ', strip=True)
        title = None
        company = None
        description = None

        json_ld = parse_json_ld(soup)
        if json_ld:
            title = json_ld.get('title')
            org = json_ld.get('hiringOrganization')
            if isinstance(org, dict):
                company = org.get('name')
            description = json_ld.get('description')
            if description:
                desc_soup = BeautifulSoup(description, 'html.parser')
                description = desc_soup.get_text(separator='\n', strip=True)

        if not title:
            t_elem = soup.find('h1', class_='top-card-layout__title') or soup.find('h1')
            if t_elem:
                title = t_elem.text.strip()
            else:
                og_title = soup.find('meta', property='og:title')
                if og_title and og_title.get('content'):
                    title = og_title['content'].strip()

        if not company:
            c_elem = soup.find('a', class_='topcard__org-name-link') or soup.find('span', class_='topcard__flavor')
            if c_elem:
                company = c_elem.text.strip()

        if not description:
            desc_element = soup.find('div', class_='description__text') or soup.find('section', class_='show-more-less-html')
            if desc_element:
                description = desc_element.get_text(separator='\n', strip=True)

        if not title or title == "Título no encontrado" or not company:
            return handle_manual_paste_fallback(url)

        return {
            'title': title,
            'company': company,
            'description': description or "Descripción no disponible",
            'raw_page_text': raw_page_text,
            'url': url
        }
    except Exception as e:
        print(f"Error al procesar LinkedIn: {e}")
        return handle_manual_paste_fallback(url)

def scrape_generic(url):
    print(f"Buscando en portal de empleos (Jora/Indeed/Gumtree/Directo): {url}")
    html_text = fetch_url_content(url)
    if not html_text:
        print("\n[!] El sitio web bloqueó el acceso directo (Protección Anti-Bot 403).")
        return handle_manual_paste_fallback(url)

    try:
        soup = BeautifulSoup(html_text, 'html.parser')
        raw_page_text = soup.get_text(separator=' ', strip=True)
        title = None
        company = None
        description = None
        
        json_ld = parse_json_ld(soup)
        if json_ld:
            title = json_ld.get('title')
            org = json_ld.get('hiringOrganization')
            if isinstance(org, dict):
                company = org.get('name')
            elif isinstance(org, str):
                company = org
            description = json_ld.get('description')
            if description:
                desc_soup = BeautifulSoup(description, 'html.parser')
                description = desc_soup.get_text(separator='\n', strip=True)

        if not title:
            t_elem = soup.find('h1') or soup.find('h2')
            if t_elem:
                title = t_elem.text.strip()
            else:
                page_title = soup.find('title')
                if page_title:
                    title = page_title.text.split('-')[0].split('|')[0].strip()

        if not company:
            meta_author = soup.find('meta', {'name': 'author'}) or soup.find('meta', {'property': 'og:site_name'})
            if meta_author and meta_author.get('content'):
                company = meta_author['content'].strip()

        if not description:
            main_sec = soup.find('main') or soup.find('article') or soup.find('div', class_=lambda c: c and 'job' in str(c).lower())
            if main_sec:
                description = main_sec.get_text(separator='\n', strip=True)
            else:
                description = raw_page_text[:3000]

        if not title or len(title) > 80 or not company or len(company) > 60:
            return handle_manual_paste_fallback(url)

        return {
            'title': title,
            'company': company,
            'description': description or "Descripción no disponible",
            'raw_page_text': raw_page_text,
            'url': url
        }
    except Exception as e:
        print(f"\n[!] Error al procesar portal: {e}")
        return handle_manual_paste_fallback(url)

def handle_manual_paste_fallback(url):
    print("\nNo te preocupes, podés pegar todo el texto del aviso de una sola vez:")
    pasted_text = get_multiline_input("PEGA EL ANUNCIO DE TRABAJO COMPLETO")
    
    if not pasted_text:
        return None

    import ai_generator
    parsed = ai_generator.parse_pasted_job_text(pasted_text)
    
    title = parsed.get("title", "Puesto de Trabajo")
    company = parsed.get("company", "Empresa General")
    description = parsed.get("description", pasted_text)
    
    print(f"\n[✓] Datos extraídos automáticamente por IA del texto pegado:")
    print(f" -> Título: {title}")
    print(f" -> Empresa: {company}\n")
    
    return {
        'title': title,
        'company': company,
        'description': description,
        'raw_page_text': pasted_text,
        'url': url
    }

def get_job_data(url):
    if "seek.com" in url:
        return scrape_seek(url)
    elif "linkedin.com" in url:
        return scrape_linkedin(url)
    else:
        return scrape_generic(url)
