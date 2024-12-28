import requests
import os
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__, static_url_path='', static_folder='../frontend/public')
CORS(app)


# Set your OpenAI API key
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Initialize scraped_data_text as a global variable
scraped_data_text = ""

@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

def scrape_website(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        soup = BeautifulSoup(response.text, 'html.parser')

        content = {
            "title": soup.title.string if soup.title else "No Title",
            "headings": [h.get_text().strip() for h in soup.find_all(['h1', 'h2', 'h3'])],
            "paragraphs": [p.get_text().strip() for p in soup.find_all('p')],
        }
        return content
    except requests.RequestException as e:
        return {"error": f"Failed to fetch the website: {str(e)}"}
    except Exception as e:
        return {"error": f"Failed to scrape the website: {str(e)}"}

@app.route("/scrape", methods=['POST'])
def scrape():
    global scraped_data_text
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400
    
    url = data.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    scraped_data = scrape_website(url)
    if "error" in scraped_data:
        return jsonify({"error": scraped_data["error"]}), 500

    # Format the scraped data without using backslashes in f-string
    sections = [
        f"Title: {scraped_data['title']}",
        "Headings:",
        *scraped_data['headings'],
        "Paragraphs:",
        *scraped_data['paragraphs']
    ]
    
    # Join with newlines to create the final text
    scraped_data_text = "\n".join(sections)
    
    return jsonify({
        "message": "Scraping successful",
        "scraped_data": scraped_data
    })

@app.route('/ask', methods=['POST'])
def ask():
    global scraped_data_text
    
    if not scraped_data_text:
        return jsonify({"error": "No scraped data available. Please scrape a website first."}), 400
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400
    
    question = data.get("question")
    if not question:
        return jsonify({"error": "No question provided"}), 400

    try:
        completion = client.chat.completions.create(
            model="gpt-4-mini",  # Make sure this is the correct model name
            messages=[
                {"role": "system", "content": scraped_data_text},
                {"role": "user", "content": f"Based on the following website data:\n\n{scraped_data_text}\n\nAnswer the question: {question}"}
            ]
        )

        answer = completion.choices[0].message.content
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"error": f"OpenAI API error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)