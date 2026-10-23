from duckduckgo_search import DDGS
from flask import Flask, jsonify, render_template_string, request
from flask_cors import CORS
from googlesearch import search as google_search

app = Flask(__name__)
CORS(app)

# HTML Web Arayüzü Template'i
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AraKiBula - Arama Motoru</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0f172a;
            --card-bg: rgba(30, 41, 59, 0.7);
            --border: rgba(255, 255, 255, 0.1);
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --accent: #38bdf8;
            --accent-hover: #0284c7;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
        body { background: var(--bg); color: var(--text); min-height: 100vh; display: flex; flex-direction: column; align-items: center; padding: 2rem 1rem; }
        
        .container { width: 100%; max-width: 800px; }
        header { text-align: center; margin-bottom: 2.5rem; }
        h1 { font-size: 2.5rem; font-weight: 700; background: linear-gradient(135deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
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

        select {
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid var(--border);
            color: var(--text-muted);
            border-radius: 10px;
            padding: 0 12px;
            outline: none;
            cursor: pointer;
        }

        button {
            background: var(--accent);
            color: #0f172a;
            border: none;
            border-radius: 10px;
            padding: 12px 24px;
            font-weight: 600;
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
            transition: transform 0.2s, border-color 0.2s;
        }
        .result-card:hover { transform: translateY(-2px); border-color: rgba(56, 189, 248, 0.4); }
        .result-card a { color: var(--accent); text-decoration: none; font-size: 1.15rem; font-weight: 600; display: inline-block; margin-bottom: 0.4rem; }
        .result-card a:hover { text-decoration: underline; }
        .result-card .url { font-size: 0.8rem; color: #10b981; margin-bottom: 0.6rem; word-break: break-all; }
        .result-card p { color: var(--text-muted); font-size: 0.92rem; line-height: 1.5; }
        
        .status-badge {
            display: inline-block;
            font-size: 0.75rem;
            padding: 2px 8px;
            border-radius: 6px;
            background: rgba(56, 189, 248, 0.1);
            color: var(--accent);
            margin-top: 8px;
        }

        .loading { text-align: center; color: var(--text-muted); padding: 2rem; display: none; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>AraKiBula</h1>
            <p class="subtitle">Hızlı, Özgür ve Kesintisiz Arama Motoru</p>
        </header>

        <div class="search-box">
            <input type="text" id="query" placeholder="Aramak istediğiniz kelimeyi yazın..." onkeypress="if(event.key==='Enter') doSearch()">
            <select id="source">
                <option value="auto">Otomatik (Yedekli)</option>
                <option value="ddg">DuckDuckGo</option>
                <option value="google">Google</option>
            </select>
            <button onclick="doSearch()">Ara</button>
        </div>

        <div class="loading" id="loading">Arama sonuçları getiriliyor...</div>
        <div class="results" id="results"></div>
    </div>

    <script>
        async function doSearch() {
            const q = document.getElementById('query').value.trim();
            const source = document.getElementById('source').value;
            const resultsDiv = document.getElementById('results');
            const loading = document.getElementById('loading');

            if (!q) return;

            resultsDiv.innerHTML = '';
            loading.style.display = 'block';

            try {
                const res = await fetch(`/search?q=${encodeURIComponent(q)}&source=${source}`);
                const data = await res.json();
                loading.style.display = 'none';

                if (data.results && data.results.length > 0) {
                    data.results.forEach(item => {
                        const card = document.createElement('div');
                        card.className = 'result-card';
                        card.innerHTML = `
                            <a href="${item.link}" target="_blank">${item.title}</a>
                            <div class="url">${item.link}</div>
                            <p>${item.snippet || 'Açıklama bulunmuyor.'}</p>
                            <span class="status-badge">${item.source}</span>
                        `;
                        resultsDiv.appendChild(card);
                    });
                } else {
                    resultsDiv.innerHTML = '<p style="text-align:center; color: var(--text-muted);">Sonuç bulunamadı.</p>';
                }
            } catch (err) {
                loading.style.display = 'none';
                resultsDiv.innerHTML = '<p style="text-align:center; color: #ef4444;">Arama yapılırken bir hata oluştu.</p>';
            }
        }
    </script>
</body>
</html>
"""


@app.route("/", methods=["GET"])
def home():
    # Ana dizinde şık Arama Arayüzünü sunar
    return render_template_string(HTML_TEMPLATE)


@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("q")
    source = request.args.get("source", "auto").lower()

    if not query:
        return jsonify({"error": "Arama sorgusu ('q') eksik."}), 400

    results = []

    # 1. DuckDuckGo Arama Fonksiyonu
    def search_ddg():
        ddg_list = []
        with DDGS() as ddgs:
            for item in ddgs.text(query, max_results=10, backend="html"):
                ddg_list.append(
                    {
                        "title": item.get("title"),
                        "link": item.get("href"),
                        "snippet": item.get("body"),
                        "source": "DuckDuckGo",
                    }
                )
        return ddg_list

    # 2. Google Arama Fonksiyonu
    def search_google():
        google_list = []
        for url in google_search(query, num_results=10):
            google_list.append(
                {
                    "title": url,
                    "link": url,
                    "snippet": "",
                    "source": "Google",
                }
            )
        return google_list

    # Seçilen kaynağa göre çalıştırma
    if source == "ddg":
        try:
            results = search_ddg()
        except Exception as e:
            return (
                jsonify({"error": "DuckDuckGo hatası", "details": str(e)}),
                500,
            )

    elif source == "google":
        try:
            results = search_google()
        except Exception as e:
            return (
                jsonify({"error": "Google hatası", "details": str(e)}),
                500,
            )

    else:  # 'auto' (Yedekli Yapı)
        try:
            results = search_ddg()
        except Exception as e:
            print(f"DuckDuckGo çalışmadı, Google'a geçiliyor: {e}")
            try:
                results = search_google()
            except Exception as g_e:
                return (
                    jsonify(
                        {
                            "error": "Arama servislerine ulaşılamadı.",
                            "details": str(g_e),
                        }
                    ),
                    500,
                )

    return jsonify(
        {"status": "success", "count": len(results), "results": results}
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
