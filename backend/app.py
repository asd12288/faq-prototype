import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from openai import OpenAI


app = Flask(__name__, static_url_path='', static_folder='../frontend/public')
CORS(app)  # Enable CORS for all routes

# Set your OpenAI API key
client = OpenAI()


@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

def scrape_website(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        content = {
            "title": soup.title.string if soup.title else "No Title",
            "headings": [h.get_text() for h in soup.find_all(['h1', 'h2', 'h3'])],
            "paragraphs": [p.get_text() for p in soup.find_all('p')],
        }
        return content
    except Exception as e:
        return {"error": f"Failed to scrape the website: {str(e)}"}

@app.route("/scrape", methods=['POST'])
def scrape():
    data = request.get_json()
    url = data.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400  # Added 400 status code for client errors

    scraped_data = scrape_website(url)
    if "error" in scraped_data:
        return jsonify({"error": scraped_data["error"]}), 500  # Added 500 status code for server errors

    # Properly formatted multiline string
    global scraped_data_text
    scraped_data_text = f"""
Title: {scraped_data['title']}

Headings:
{'\n'.join(scraped_data['headings'])}

Paragraphs:
{'\n'.join(scraped_data['paragraphs'])}
"""
    return jsonify({"message": "Scraping successful", "scraped_data": scraped_data})


# Route to handle the question
@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    question = data.get("question")
    if not question:
        return jsonify({"error": "No question provided"}), 400


    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": scraped_data_text},
                {
                    "role": "user",
                    "content": f"based on the following website data:\n\n{scraped_data_text}\n\nAnswer the question: {question}",
                }
            ]
        )

        answer = completion.choices[0].message.content
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
