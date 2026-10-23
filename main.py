import re
from duckduckgo_search import DDGS
from flask import Flask, jsonify, render_template_string, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Sadece bu pazar yerleri/karşılaştırma siteleri kabul edilecek
ALLOWED_DOMAINS = {
    "akakce": "Akakçe",
    "cimri": "Cimri",
    "trendyol": "Trendyol",
    "hepsiburada": "Hepsiburada",
    "amazon": "Amazon TR",
    "n11": "N11",
    "pazarama": "Pazarama",
    "ciceksepeti": "Çiçeksepeti",
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AraKiBula - Fiyat Bulucu</title>
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
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>AraKiBula</h1>
            <p class="subtitle">E-Ticaret ve Fiyat Karşılaştırma Arama Motoru</p>
        </header>

        <div class="search-box">
            <input type="text" id="query" placeholder="Aradığınız ürünü yazın (ör: Logitech MX Master 3S)..." onkeypress="if(event.key==='Enter') doSearch()">
            <button onclick="doSearch()">Fiyat Bul</button>
        </div>

        <div class="loading" id="loading">Fiyatlar ve pazar yerleri taranıyor...</div>
        <div class="results" id="results"></div>
    </div>

    <script>
        async function doSearch() {
            const q = document.getElementById('query').value.trim();
            const resultsDiv = document.getElementById('results');
            const loading = document.getElementById('loading');

            if (!q) return;

            resultsDiv.innerHTML = '';
            loading.style.display = 'block';

            try {
                const res = await fetch(`/search?q=${encodeURIComponent(q)}`);
                const data = await res.json();
                loading.style.display = 'none';

                if (data.results && data.results.length > 0) {
                    data.results.forEach((item) => {
                        const card = document.createElement('div');
                        card.className = 'result-card';
                        
                        let priceHtml = item.price > 0 
                            ? `<div class="price-tag">${item.price.toLocaleString('tr-TR')} TL'den başlayan fiyatlar</div>`
                            : `<div class="price-tag" style="color: var(--text-muted); font-size:1rem;">Fiyat Detayları İçin Tıklayın</div>`;

                        card.innerHTML = `
                            <span class="source-badge">${item.source_site}</span>
                            ${priceHtml}
                            <a href="${item.link}" target="_blank">${item.title}</a>
                            <p>${item.snippet || 'Ürün detayı bulunmuyor.'}</p>
                        `;
                        resultsDiv.appendChild(card);
                    });
                } else {
                    resultsDiv.innerHTML = '<p style="text-align:center; color: var(--text-muted);">Pazar yerlerinde veya karşılaştırma sitelerinde uygun sonuç bulunamadı.</p>';
                }
            } catch (err) {
                loading.style.display = 'none';
                resultsDiv.innerHTML = '<p style="text-align:center; color: #ef4444;">Fiyatlar taranırken bir hata oluştu.</p>';
            }
        }
    </script>
</body>
</html>
"""


def extract_price(text):
    """Metindeki TL / ₺ fiyatlarını bulur."""
    pattern = r"(\d{1,3}(?:\.\d{3})*(?:,\d{1,2})?)\s*(?:TL|TL'den|₺)"
    matches = re.findall(pattern, text)

    prices = []
    for match in matches:
        try:
            clean_price = match.replace(".", "").replace(",", ".")
            val = float(clean_price)
            if 10 <= val <= 500000:
                prices.append(val)
        except ValueError:
            continue

    return min(prices) if prices else 0


def identify_store(link):
    """Link içerisinden hangi e-ticaret/karşılaştırma sitesi olduğunu tespit eder."""
    link_lower = link.lower()
    for domain, name in ALLOWED_DOMAINS.items():
        if domain in link_lower:
            return name
    return None
