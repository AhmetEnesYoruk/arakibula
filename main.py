import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Google API ve Search Engine ID tanımlamaları
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyCMw9ULeSudIiaoU6Z3bRc9QG6JhXdKSnM")
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID", "704ea1190e63442d4")

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "ok", "message": "AraKiBula API servisi çalışıyor!"})

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q')
    if not query:
        return jsonify({"error": "Lütfen 'q' parametresi ile bir arama terimi belirtin."}), 400

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': GOOGLE_API_KEY,
        'cx': SEARCH_ENGINE_ID,
        'q': query
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if response.status_code != 200:
            return jsonify({"error": "Google API Hatası", "details": data}), response.status_code

        results = []
        items = data.get('items', [])
        for item in items:
            results.append({
                'title': item.get('title'),
                'link': item.get('link'),
                'snippet': item.get('snippet')
            })

        return jsonify({
            'query': query,
            'total_results': len(results),
            'results': results
        })

    except Exception as e:
        return jsonify({"error": "Sunucu hatası", "details": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
