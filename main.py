import urllib.parse
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
import httpx
from bs4 import BeautifulSoup
import uvicorn

app = FastAPI(title="AraKiBula - E-Ticaret Arama Motoru")

def search_duckduckgo(query: str):
    results = []
    encoded_query = urllib.parse.quote(query)
    url = f"https://html.duckduckgo.com/html/?q={encoded_query}+site:trendyol.com+OR+site:hepsiburada.com+OR+site:amazon.com.tr"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://html.duckduckgo.com/"
    }

    try:
        with httpx.Client(headers=headers, timeout=12.0, follow_redirects=True) as client:
            response = client.get(url)
            
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            snippets = soup.select(".result")

            for item in snippets[:12]:
                try:
                    title_elem = item.select_one(".result__title")
                    link_elem = item.select_one(".result__url")
                    snippet_elem = item.select_one(".result__snippet")

                    title = title_elem.get_text(strip=True) if title_elem else ""
                    raw_link = link_elem.get("href", "") if link_elem else ""
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                    if "//duckduckgo.com/l/?" in raw_link:
                        parsed = urllib.parse.parse_qs(urllib.parse.urlparse(raw_link).query)
                        if "uddg" in parsed:
                            raw_link = parsed["uddg"][0]

                    site = "Diğer"
                    if "trendyol.com" in raw_link:
                        site = "Trendyol"
                    elif "hepsiburada.com" in raw_link:
                        site = "Hepsiburada"
                    elif "amazon.com.tr" in raw_link:
                        site = "Amazon"
                    elif "n11.com" in raw_link:
                        site = "N11"

                    if title and raw_link.startswith("http"):
                        results.append({
                            "site": site,
                            "title": title,
                            "link": raw_link,
                            "details": snippet
                        })
                except Exception:
                    continue
    except Exception as e:
        print(f"Arama hatası: {e}")

    return results

@app.get("/", response_class=HTMLResponse)
def home_page():
    return """
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AraKiBula - Fiyat Karşılaştırma</title>
        <style>
            * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
            body { background-color: #f4f6f9; margin: 0; padding: 15px; }
            .header { text-align: center; margin-bottom: 20px; }
            .header h1 { color: #2c3e50; margin-bottom: 5px; }
            .search-box { display: flex; gap: 10px; max-width: 600px; margin: 0 auto 20px auto; }
            input { flex: 1; padding: 12px 15px; border: 1px solid #ddd; border-radius: 8px; font-size: 16px; outline: none; }
            button { background: #ff6000; color: white; border: none; padding: 12px 20px; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; }
            .results { max-width: 600px; margin: 0 auto; }
            .card { background: white; padding: 15px; border-radius: 10px; margin-bottom: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
            .tag { display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; color: white; margin-bottom: 8px; }
            .Trendyol { background: #f27a1a; }
            .Hepsiburada { background: #ff6000; }
            .Amazon { background: #232f3e; }
            .N11 { background: #e31e24; }
            .Diğer { background: #7f8c8d; }
            .title { font-weight: 600; color: #333; margin-bottom: 5px; text-decoration: none; display: block; }
            .details { font-size: 13px; color: #666; margin-bottom: 10px; }
            .btn-link { display: inline-block; background: #27ae60; color: white; text-decoration: none; padding: 8px 12px; border-radius: 5px; font-size: 13px; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔍 AraKiBula</h1>
            <p>E-Ticaret Sitelerinde Tek Tıkla Arama</p>
        </div>
        <div class="search-box">
            <input type="text" id="query" placeholder="Ürün adı yazın (Örn: Kulaklık)">
            <button onclick="doSearch()">Ara</button>
        </div>
        <div id="results" class="results"></div>

        <script>
            async function doSearch() {
                const q = document.getElementById('query').value;
                if(!q) return;
                const resContainer = document.getElementById('results');
                resContainer.innerHTML = '<p style="text-align:center;">Aranıyor...</p>';
                
                try {
                    const res = await fetch('/search?q=' + encodeURIComponent(q));
                    const data = await res.json();
                    
                    if(data.results.length === 0) {
                        resContainer.innerHTML = '<p style="text-align:center;">Sonuç bulunamadı.</p>';
                        return;
                    }
                    
                    let html = '';
                    data.results.forEach(item => {
                        html += `
                            <div class="card">
                                <span class="tag ${item.site}">${item.site}</span>
                                <a href="${item.link}" target="_blank" class="title">${item.title}</a>
                                <div class="details">${item.details}</div>
                                <a href="${item.link}" target="_blank" class="btn-link">Ürünü İncele ➔</a>
                            </div>
                        `;
                    });
                    resContainer.innerHTML = html;
                } catch(e) {
                    resContainer.innerHTML = '<p style="text-align:center; color:red;">Arama sırasında hata oluştu.</p>';
                }
            }
        </script>
    </body>
    </html>
    """

@app.get("/search")
def search_products(q: str = Query(..., description="Aranacak ürün")):
    res = search_duckduckgo(q)
    return {
        "query": q,
        "total_results": len(res),
        "results": res
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
