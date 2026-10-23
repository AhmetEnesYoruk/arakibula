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
    <title>AraKiBula - Akıllı Fiyat Karşılaştırma Portalı</title>
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

        .platforms-grid {
            margin-top: 2rem;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.25rem;
        }

        .platform-card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: transform 0.2s, border-color 0.2s;
        }

        .platform-card:hover {
            transform: translateY(-4px);
            border-color: rgba(56, 189, 248, 0.4);
        }

        .platform-info h3 {
            font-size: 1.25rem;
            color: #f8fafc;
            margin-bottom: 0.4rem;
        }

        .platform-info p {
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-bottom: 1.25rem;
        }

        .btn-redirect {
            display: inline-block;
            text-align: center;
            background: rgba(56, 189, 248, 0.1);
            color: #38bdf8;
            border: 1px solid rgba(56, 189, 248, 0.2);
            padding: 10px 16px;
            border-radius: 8px;
            font-weight: 600;
            text-decoration: none;
            transition: all 0.2s;
        }

        .btn-redirect:hover {
            background: #38bdf8;
            color: #0f172a;
        }

        .open-all-btn {
            width: 100%;
            margin-top: 1.5rem;
            background: #10b981;
            color: #0f172a;
            font-size: 1rem;
        }

        .open-all-btn:hover {
            background: #059669;
            color: white;
        }

        .placeholder-msg {
            text-align: center;
            color: var(--text-muted);
            margin-top: 3rem;
            font-size: 0.95rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>AraKiBula</h1>
            <p class="subtitle">Akıllı Fiyat ve Mağaza Karşılaştırma Portalı</p>
        </header>

        <div class="search-box">
            <input type="text" id="query" placeholder="Aradığınız ürünün adını yazın (ör: Logitech MX Master 3S)..." onkeypress="if(event.key==='Enter') generateLinks()">
            <button onclick="generateLinks()">Karşılaştır</button>
        </div>

        <div id="results-container" style="display: none;">
            <button class="open-all-btn" onclick="openAllTabs()">Tüm Platformlarda Aynı Anda Ara (Yeni Sekmelerde Aç)</button>
            <div class="platforms-grid" id="platforms-grid"></div>
        </div>

        <div id="placeholder" class="placeholder-msg">
            Aramak istediğiniz ürünü yukarıya yazıp "Karşılaştır" butonuna basın.
        </div>
    </div>

    <script>
        let currentLinks = [];

        function generateLinks() {
            const q = document.getElementById('query').value.trim();
            if (!q) return;

            const encodedQuery = encodeURIComponent(q
        
