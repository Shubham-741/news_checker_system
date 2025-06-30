import requests
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

API_KEY = ''  # Replace with your API key
SEARCH_ENGINE_ID = ''  # Replace with your CSE ID

@app.route('/')
def index():
    return render_template('index.html')


def search_news(query):
    """Search news using Google Custom Search API."""
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': API_KEY,
        'cx': SEARCH_ENGINE_ID,
        'q': query,
        'num': 5,
        'gl': 'us',  # restrict to US, can change
        'hl': 'en'
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return None, f"Search API error: {response.status_code}"
    return response.json(), None

def classify_based_on_results(results_json):
    """
    Very simple heuristic:
    - If results contain fact-check sites denying the news => FAKE
    - If results contain trusted news confirming news => TRUE
    - Else UNKNOWN
    """
    fake_indicators = ['snopes.com', 'factcheck.org', 'politifact.com', 'hoax-slayer.com']
    trusted_news_sites = ['bbc.com', 'reuters.com', 'apnews.com', 'cnn.com', 'nytimes.com', 'theguardian.com']

    fake_count = 0
    true_count = 0
    links_true = []
    links_fake = []

    items = results_json.get('items', [])

    for item in items:
        link = item.get('link', '')
        snippet = item.get('snippet', '').lower()

        # Check if any fake-checking domain is in link
        if any(fake_site in link for fake_site in fake_indicators):
            fake_count += 1
            links_fake.append(link)
        elif any(trusted_site in link for trusted_site in trusted_news_sites):
            true_count += 1
            links_true.append(link)

    if fake_count > true_count:
        verdict = "❌ This news appears to be FAKE."
        supporting_links = links_fake
    elif true_count > 0:
        verdict = "✅ This news appears to be TRUE."
        supporting_links = links_true
    else:
        verdict = "Please review these resources."
        supporting_links = [item.get('link') for item in items]

    return verdict, supporting_links

@app.route('/check-news', methods=['POST'])
def check_news():
    data = request.get_json()
    article = data.get('article', '').strip()

    if not article:
        return jsonify({"error": "Article content is required."}), 400

    # Use the article headline or first 50 words for searching
    search_query = ' '.join(article.split()[:50])

    search_results, error = search_news(search_query)
    if error:
        return jsonify({"error": error}), 500

    verdict, links = classify_based_on_results(search_results)

    return jsonify({
        "verdict": verdict,
        "supporting_links": links[:5]  # return top 5 links
    })

if __name__ == '__main__':
    app.run(debug=True)
