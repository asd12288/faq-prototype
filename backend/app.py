import requests
import os
import json
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__, static_url_path='', static_folder='../frontend/public')
CORS(app)

# Set your OpenAI API key
client = OpenAI()

# Initialize scraped_data_text and scraped_faqs as global variables
scraped_data_text = ""
scraped_faqs = []



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
    global scraped_data_text, scraped_faqs
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400
    
    url = data.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    scraped_data = scrape_website(url)
    if "error" in scraped_data:
        return jsonify({"error": scraped_data["error"]}), 500

    # Convert scraped data to text
    sections = [
        f"Title: {scraped_data['title']}",
        "Headings:",
        *scraped_data['headings'],
        "Paragraphs:",
        *scraped_data['paragraphs']
    ]
    scraped_data_text = "\n".join(filter(None, sections))
    
    # Generate 3 most relevant FAQs
    try:
        faq_completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Return JSON in the exact format { \"message\": \"Scraping successful\", \"scraped_data\": \"...\", \"faqs\": [ { \"question\": \"...\", \"answer\": \"...\" } ] }. and always anser in"},
                {"role": "user", "content": f"Content:\n\n{scraped_data_text}\n\nGenerate 3 relevant FAQ questions and answers. answer always in hebrew"}
            ]
        )
        scraped_faqs_str = faq_completion.choices[0].message.content

        # Convert the string from GPT to JSON in your prompt or parse it here, e.g.:
        try:
            scraped_faqs_dict = json.loads(scraped_faqs_str)
            scraped_faqs = scraped_faqs_dict.get("faqs", [])
        except json.JSONDecodeError:
            scraped_faqs = []
    except Exception as e:
        return jsonify({"error": f"FAQ generation error: {str(e)}"}), 500
    
    return jsonify({
        "message": "Scraping successful",
        "scraped_data": scraped_data_text,
        "faqs": scraped_faqs
    })

@app.route('/ask', methods=['POST'])
def ask():
    global scraped_data_text, scraped_faqs
    
    if not scraped_data_text:
        return jsonify({"error": "No scraped data available. Please scrape a website first."}), 400
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400
    
    question = data.get("question")
    if not question:
        return jsonify({"error": "No question provided"}), 400

    try:
        # The main answer
        main_completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Based on the following website data:\n\n{scraped_data_text}\n\nAnswer the question: {question} if the answer is not in the data or the question is not relevent answer with: the data is not provided or the question is not relevant."}
            ]
        )
        main_answer = main_completion.choices[0].message.content
        
        return jsonify({
            "main_answer": main_answer,
            "faqs": scraped_faqs
        })
    except Exception as e:
        return jsonify({"error": f"OpenAI API error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0',      # Allows external connections
        port=8080,           # Custom port
        debug=False,         # Disable debug mode in production
        threaded=True)       # Enable threading)