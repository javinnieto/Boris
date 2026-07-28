import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

def test_seek_html():
    kw = quote("Mechanical Engineer")
    where = quote("Melbourne VIC")
    url = f"https://www.seek.com.au/{kw-jobs}/in-{where}?sortmode=CreatedAt" if False else f"https://www.seek.com.au/jobs?keywords={kw}&where={where}&sortmode=CreatedAt"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    }
    try:
        from curl_cffi import requests as crequests
        r = crequests.get(url, impersonate="chrome120", timeout=12)
        print("Seek HTML status:", r.status_code)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            articles = soup.find_all('article')
            print(f"Found {len(articles)} job articles on Seek HTML")
            for art in articles[:3]:
                title_elem = art.find(attrs={"data-automation": "jobTitle"}) or art.find('a')
                company_elem = art.find(attrs={"data-automation": "jobCompany"})
                if title_elem:
                    t = title_elem.text.strip()
                    href = "https://www.seek.com.au" + title_elem.get('href', '').split('?')[0]
                    c = company_elem.text.strip() if company_elem else "Empresa"
                    print(f" - {t} | {c} | {href}")
    except Exception as e:
        print("Seek HTML error:", e)

if __name__ == "__main__":
    test_seek_html()
