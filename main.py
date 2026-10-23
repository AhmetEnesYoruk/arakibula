from flask import Flask, render_template_string
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AraKiBula - Akıllı Fiyat Bulucu</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0f172a;
            --card-bg: rgba(30, 41, 59, 0.7);
            --border: rgba(255, 255, 255, 0.1);
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --accent: #eab308;
            --accent-hover: #ca8a04;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
        body { background: var(--bg); color: var(--text); min-height: 100vh; display: flex; flex-direction: column; align-items: center; padding: 2rem 1rem; }
        
        .container { width: 100%; max-width: 850px; }
        header { text-align: center; margin-bottom: 2.5rem; }
        h1 { font-size: 2.5rem; font-weight: 700; background: linear-gradient(135deg, #eab308, #38bdf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        p.subtitle { color: var(--text-muted); margin-top: 0.5rem; font-size: 0.95rem; }

        .search-box {
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 8px;
            display: flex;
            gap: 8px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        }

        input[type="text"] {
            flex: 1;
            background: transparent;
            border: none;
            outline: none;
            color: var(--text);
            padding: 12px 16px;
            font-size: 1rem;
        }

        button {
            background: var(--accent);
            color: #0f172a;
            border: none;
            border-radius: 10px;
            padding: 12px 24px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s;
        }

        button:hover { background: var(--accent-hover); color: white; }

        .results { margin-top: 2rem; display: flex; flex-direction: column; gap: 1rem; }
        .result-card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.25rem;
            position: relative;
            transition: transform 0.2s, border-color 0.2s;
        }
        .result-card:hover { transform: translateY(-2px); border-color: rgba(234, 179, 8, 0.4); }

        .price-tag {
            font-size: 1.4rem;
            font-weight: 700;
            color: #34d399;
            margin-bottom: 0.3rem;
        }

        .source-badge {
            display: inline-block;
            font-size: 0.75rem;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 6px;
            background: rgba(56, 189, 248, 0.1);
            color: #38bdf8;
            margin-bottom: 8px;
        }

        .result-card a { color: #f8fafc; text-decoration: none; font-size: 1.1rem; font-weight: 600; display: block; margin-bottom: 0.4rem; }
        .result-card a:hover { color: var(--accent); }
        .result-card p { color: var(--text-muted); font-size: 0.9rem; line-height: 1.4; }

        .loading { text-align: center; color: var(--text-muted); padding: 2rem; display: none; }
        .error-msg { text-align: center; color: #ef4444; padding: 1.5rem; background: rgba(239, 68, 68, 0.1); border-radius: 12px; border: 1px solid rgba(239, 68, 68, 0.2); }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>AraKiBula</h1>
            <p class="subtitle">İstemci Tabanlı Akıllı Fiyat Karşılaştırma</p>
        </header>

        <div class="search-box">
            <input type="text" id="query" placeholder="Aradığınız ürünü yazın (ör: Logitech MX Master 3S)..." onkeypress="if(event.key==='Enter') doSearch()">
            <button onclick="doSearch()">Fiyat Bul</button>
        </div>

        <div class="loading" id="loading">Fiyatlar ve pazar yerleri taranıyor...</div>
        <div class="results" id="results"></div>
    </div>

    <script>
        const ALLOWED_DOMAINS = {
            "akakce.com": "Akakçe",
            "cimri.com": "Cimri",
            "trendyol.com": "Trendyol",
            "hepsiburada.com": "Hepsiburada",
            "amazon.com.tr": "Amazon TR",
            "n11.com": "N11",
            "pazarama.com": "Pazarama",
            "ciceksepeti.com": "Çiçeksepeti"
        };

        function extractPrice(text) {
            const pattern = /(\d{1,3}(?:\.\d{3})*(?:,\d{1,2})?)\s*(?:TL|TL'den|₺)/gi;
            let matches = [];
            let match;
            while ((match = pattern.exec(text)) !== null) {
                try {
                    let cleanPrice = match[1].replace(/\./g, "").replace(",", ".");
                    let val = parseFloat(cleanPrice);
                    if (val >= 10 && val <= 500000) {
                        matches.push(val);
                    }
                } catch(e) {}
            }
            return matches.length > 0 ? Math.min(...matches) : 0;
        }

        function identifyStore(link) {
            const lowerLink = link.toLowerCase();
            for (const [domain, name] of Object.entries(ALLOWED_DOMAINS)) {
                if (lowerLink.includes(domain)) return name;
            }
            return null;
        }

        async function doSearch() {
            const q = document.getElementById('query').value.trim();
            const resultsDiv = document.getElementById('results');
            const loading = document.getElementById('loading');

            if (!q) return;

            resultsDiv.innerHTML = '';
            loading.style.display = 'block';

            try {
                const targetQuery = encodeURIComponent(`${q} (site:akakce.com OR site:cimri.com OR site:trendyol.com OR site:hepsiburada.com OR site:amazon.com.tr OR site:n11.com)`);
                const corsProxyUrl = `https://api.allorigins.win/get?url=${encodeURIComponent('https://html.duckduckgo.com/html/?q=' + targetQuery)}`;

                const res = await fetch(corsProxyUrl);
                const data = await res.json();
                loading.style.display = 'none';

                if (!data.contents) {
                    resultsDiv.innerHTML = '<p style="text-align:center; color: var(--text-muted);">Arama sonucu alınamadı.</p>';
                    return;
                }

                const parser = new DOMParser();
                const doc = parser.parseFromString(data.contents, 'text/html');
                const links = doc.querySelectorAll('.result__body');

                let results = [];

                links.forEach(el => {
                    const titleEl = el.querySelector('.result__title a');
                    const snippetEl = el.querySelector('.result__snippet');

                    if (titleEl) {
                        let link = titleEl.getAttribute('href') || '';
                        
                        // DuckDuckGo yönlendirme URL'sini temizle
                        if (link.includes('uddg=')) {
                            const urlParams = new URLSearchParams(link.split('?')[1]);
                            link = urlParams.get('uddg') || link;
                        }

                        const title = titleEl.innerText.trim();
                        const snippet = snippetEl ? snippetEl.innerText.trim() : '';

                        const storeName = identifyStore(link);
                        if (storeName) {
                            const price = extractPrice(`${title} ${snippet}`);
                            if (!results.some(r => r.link === link)) {
                                results.push({ title, link, snippet, price, storeName });
                            }
                        }
                    }
                });

                results.sort((a, b) => {
                    if (a.price === 0) return 1;
                    if (b.price === 0) return -1;
                    return a.price - b.price;
                });

                if (results.length > 0) {
                    results.forEach(item => {
                        const card = document.createElement('div');
                        card.className = 'result-card';

                        let priceHtml = item.price > 0 
                            ? `<div class="price-tag">${item.price.toLocaleString('tr-TR')} TL'den başlayan fiyatlar</div>`
                            : `<div class="price-tag" style="color: var(--text-muted); font-size:1rem;">Fiyat Detayları İçin Tıklayın</div>`;

                        card.innerHTML = `
                            <span class="source-badge">${item.storeName}</span>
                            ${priceHtml}
                            <a href="${item.link}" target="_blank">${item.title}</a>
                            <p>${item.snippet || 'Açıklama bulunmuyor.'}</p>
                        `;
                        resultsDiv.appendChild(card);
                    });
                } else {
                    resultsDiv.innerHTML = '<p style="text-align:center; color: var(--text-muted);">Pazar yerlerinde bu ürün için doğrudan sonuç bulunamadı.</p>';
                }

            } catch (err) {
                loading.style.display = 'none';
                resultsDiv.innerHTML = `<div class="error-msg">Arama sırasında bir hata oluştu: ${err.message}</div>`;
            }
        }
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def home():
    return render_template_string(HTML_TEMPLATE)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
