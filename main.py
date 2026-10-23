import re
from duckduckgo_search import DDGS
from flask import Flask, jsonify, render_template_string, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Hedef E-Ticaret Siteleri
TARGET_STORES = [
    "trendyol.com",
    "hepsiburada.com",
    "amazon.com.tr",
    "n11.com",
    "pazarama.com",
    "ciceksepeti.com",
]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AraKiBula - Fiyat Kıyaslama Motoru</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0f172a;
            --card-bg: rgba(30, 41, 59, 0.7);
            --border: rgba(255, 255, 255, 0.1);
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --accent: #10b981;
            --accent-hover: #059669;
            --cheap-badge: #eab308;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
        body { background: var(--bg); color: var(--text); min-height: 100vh; display: flex; flex-direction: column; align-items: center; padding: 2rem 1rem; }
        
        .container { width: 100%; max-width: 850px; }
        header { text-align: center; margin-bottom: 2.5rem; }
        h1 { font-size: 2.5rem; font-weight: 700; background: linear-gradient(135deg, #10b981, #38bdf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
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
        .result-card:hover { transform: translateY(-2px); border-color: rgba(16, 185, 129, 0.4); }
        .result-card.cheapest { border: 2px solid var(--cheap-badge); background: rgba(234, 179, 8, 0.05); }

        .price-tag {
            font-size: 1.4rem;
            font-weight: 700;
            color: #34d399;
            margin-bottom: 0.3rem;
        }

        .badge-cheapest {
            position: absolute;
            top: 12px;
            right: 12px;
            background: var(--cheap-badge);
            color: #000;
            font-size: 0.75rem;
            font-weight: 800;
            padding: 4px 10px;
            border-radius: 20px;
            text-transform: uppercase;
        }

        .result-card a { color: #38bdf8; text-decoration: none; font-size: 1.1rem; font-weight: 600; display: inline-block; margin-bottom: 0.4rem; }
        .result-card a:hover { text-decoration: underline; }
        .result-card .store { font-size: 0.85rem; color: var(--text-muted); font-weight: 600; margin-bottom: 0.5rem; }
        .result-card p { color: var(--text-muted); font-size: 0.9rem; line-height: 1.4; }

        .loading { text-align: center; color: var(--text-muted); padding: 2rem; display: none; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>AraKiBula</h1>
            <p class="subtitle">E-Ticaret Mağazalarında Akıllı Fiyat Karşılaştırma</p>
        </header>

        <div class="search-box">
            <input type="text" id="query" placeholder="Aradığınız ürünün adını yazın (ör: Logitech MX Master 3S)..." onkeypress="if(event.key==='Enter') doSearch()">
            <button onclick="doSearch()">En Ucuzunu Bul</button>
        </div>

        <div class="loading" id="loading">Pazar yerlerinde fiyatlar taranıyor ve sıralanıyor...</div>
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
                    data.results.forEach((item, index) => {
                        const isCheapest = index === 0 && item.price > 0;
                        const card = document.createElement('div');
                        card.className = `result-card ${isCheapest ? 'cheapest' : ''}`;
                        
                        let priceHtml = item.price > 0 
                            ? `<div class="price-tag">${item.price.toLocaleString('tr-TR')} TL</div>`
                            : `<div class="price-tag" style="color: var(--text-muted); font-size:1rem;">Fiyat Sitede İnceleyin</div>`;

                        card.innerHTML = `
                            ${isCheapest ? '<span class="badge-cheapest">EN UCUZ SEÇENEK</span>' : ''}
                            ${priceHtml}
                            <a href="${item.link}" target="_blank">${item.title}</a>
                            <div class="store">Mağaza: ${item.store}</div>
                            <p>${item.snippet || 'Ürün açıklaması bulunmuyor.'}</p>
                        `;
                        resultsDiv.appendChild(card);
                    });
                } else {
                    resultsDiv.innerHTML = '<p style="text-align:center; color: var(--text-muted);">Pazar yerlerinde bu ürün bulunamadı veya listelenmedi.</p>';
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
    """Metin içindeki TL / ₺ fiyat formatlarını ayıklar."""
    # Örn: 1.250 TL, 1250,00 TL, 1.250,50 TL, ₺1.250
    pattern = r"(?:₺\s*|TL\s*|\b)(\d{1,3}(?:\.\d{3})*(?:,\d{1,2})?)\s*(?:TL|₺|\b)"
    matches = re.findall(pattern, text)

    prices = []
    for match in matches:
        try:
            # Türkçe sayı formatını dönüştür (1.250,50 -> 1250.50)
            clean_price = match.replace(".", "").replace(",", ".")
            val = float(clean_price)
            # Mantıklı bir ürün fiyatı aralığı filtresi (ör: 10 TL ile 500.000 TL arası)
            if 10 <= val <= 500000:
                prices.append(val)
        except ValueError:
            continue

    return min(prices) if prices else 0


def detect_store(url):
    """URL'den mağaza adını çıkartır."""
    for store in TARGET_STORES:
        if store in url:
            name = store.split(".")[0].capitalize()
            if name == "Amazon":
                return "Amazon TR"
            return name
    return "Pazar Yeri"


@app.route("/", methods=["GET"])
def home():
    return render_template_string(HTML_TEMPLATE)


@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("q")
    if not query:
        return jsonify({"error": "Sorgu eksik"}), 400

    # E-Ticaret odaklı arama sorgusu oluşturma
    site_filter = " OR ".join([f"site:{store}" for store in TARGET_STORES])
    ecommerce_query = f"{query} ({site_filter})"

    results = []
    try:
        with DDGS() as ddgs:
            raw_results = ddgs.text(
                ecommerce_query, max_results=15, backend="html"
            )
            for item in raw_results:
                title = item.get("title", "")
                snippet = item.get("body", "")
                link = item.get("href", "")

                # Fiyatı hem başlıktan hem açıklamadan ara
                price = extract_price(f"{title} {snippet}")
                store = detect_store(link)

                results.append(
                    {
                        "title": title,
                        "link": link,
                        "snippet": snippet,
                        "price": price,
                        "store": store,
                    }
                )

        # Fiyatı bulunanları ucuzdan pahalıya sırala
        results.sort(
            key=lambda x: x["price"] if x["price"] > 0 else float("inf")
        )

    except Exception as e:
        return jsonify({"error": "Arama hatası", "details": str(e)}), 500

    return jsonify(
        {"status": "success", "count": len(results), "results": results}
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
