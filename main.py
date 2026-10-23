import urllib.parse
from fastapi import FastAPI, Query
import httpx
from bs4 import BeautifulSoup
import uvicorn

app = FastAPI(title="E-Ticaret Arama Motoru")

def search_all_stores(query: str):
    results = []
    encoded_query = urllib.parse.quote(query)
    # Akakçe / Google Shopping tarzı çoklu site fiyat arama yapısı
    url = f"https://html.duckduckgo.com/html/?q={encoded_query}+site:trendyol.com+OR+site:hepsiburada.com+OR+site:amazon.com.tr+fiyat"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9"
    }

    try:
        with httpx.Client(headers=headers, timeout=10.0, follow_redirects=True) as client:
            response = client.get(url)
            
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            snippets = soup.select(".result")

            for item in snippets[:10]:
                try:
                    title_elem = item.select_one(".result__title")
                    link_elem = item.select_one(".result__url")
                    snippet_elem = item.select_one(".result__snippet")

                    title = title_elem.get_text(strip=True) if title_elem else ""
                    raw_link = link_elem.get("href", "") if link_elem else ""
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                    # Mağaza tespiti
                    site = "Diğer"
                    if "trendyol.com" in raw_link:
                        site = "Trendyol"
                    elif "hepsiburada.com" in raw_link:
                        site = "Hepsiburada"
                    elif "amazon.com.tr" in raw_link:
                        site = "Amazon"
                    elif "n11.com" in raw_link:
                        site = "N11"

                    if title:
                        results.append({
                            "site": site,
                            "title": title,
                            "price": "Sitede Gör", # Direkt link ile fiyata yönlendirir
                            "link": raw_link,
                            "details": snippet
                        })
                except Exception:
                    continue

    except Exception as e:
        print(f"Arama Hatası: {e}")

    return results

@app.get("/search")
def search_products(q: str = Query(..., description="Aranacak ürün")):
    res = search_all_stores(q)
    return {
        "query": q,
        "total_results": len(res),
        "results": res
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)