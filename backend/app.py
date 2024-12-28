import os
import sys
import logging
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from openai import OpenAI

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_url_path='', static_folder='../frontend/public')
CORS(app)

# Log OpenAI API key status (don't log the actual key!)
api_key = os.getenv('OPENAI_API_KEY')
logger.info(f"OpenAI API key present: {api_key is not None}")

try:
    client = OpenAI(api_key=api_key)
    logger.info("OpenAI client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize OpenAI client: {str(e)}")

@app.route("/scrape", methods=['POST'])
def scrape():
    global scraped_data_text
    
    logger.info("Received scrape request")
    try:
        data = request.get_json()
        if not data:
            logger.error("No JSON data provided")
            return jsonify({"error": "No JSON data provided"}), 400
        
        url = data.get("url")
        if not url:
            logger.error("No URL provided")
            return jsonify({"error": "No URL provided"}), 400

        logger.info(f"Attempting to scrape URL: {url}")
        scraped_data = scrape_website(url)
        
        if "error" in scraped_data:
            logger.error(f"Scraping error: {scraped_data['error']}")
            return jsonify({"error": scraped_data["error"]}), 500

        sections = [
            f"Title: {scraped_data['title']}",
            "Headings:",
            *scraped_data['headings'],
            "Paragraphs:",
            *scraped_data['paragraphs']
        ]
        
        scraped_data_text = "\n".join(sections)
        logger.info("Scraping successful")
        
        return jsonify({
            "message": "Scraping successful",
            "scraped_data": scraped_data
        })
    except Exception as e:
        logger.error(f"Unexpected error in scrape endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/ask', methods=['POST'])
def ask():
    global scraped_data_text
    
    logger.info("Received ask request")
    try:
        if not scraped_data_text:
            logger.error("No scraped data available")
            return jsonify({"error": "No scraped data available. Please scrape a website first."}), 400
        
        data = request.get_json()
        if not data:
            logger.error("No JSON data provided")
            return jsonify({"error": "No JSON data provided"}), 400
        
        question = data.get("question")
        if not question:
            logger.error("No question provided")
            return jsonify({"error": "No question provided"}), 400

        logger.info(f"Sending request to OpenAI with question: {question}")
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Using a standard model name
            messages=[
                {"role": "system", "content": scraped_data_text},
                {"role": "user", "content": f"Based on the following website data:\n\n{scraped_data_text}\n\nAnswer the question: {question}"}
            ]
        )

        answer = completion.choices[0].message.content
        logger.info("Successfully received answer from OpenAI")
        return jsonify({"answer": answer})
    except Exception as e:
        logger.error(f"Error in ask endpoint: {str(e)}")
        return jsonify({"error": f"OpenAI API error: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port)