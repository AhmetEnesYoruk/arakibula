from duckduckgo_search import DDGS
from flask import Flask, jsonify, request
from googlesearch import search as google_search

app = Flask(__name__)


@app.route("/", methods=["GET"])
def home():
    return jsonify(
        {
            "status": "ok",
            "message": "AraKiBula API servisi yayında!",
            "endpoints": {"search": "/search?q=aranacak_kelime"},
        }
    )


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
            for item in ddgs.text(query, max_results=10):
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
                jsonify(
                    {"error": "DuckDuckGo hatası", "details": str(e)}
                ),
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
