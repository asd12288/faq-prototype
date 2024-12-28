import os
import sys
import logging
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import openai

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize the Flask app
app = Flask(__name__, static_url_path='', static_folder='../frontend/public')
CORS(app)

# Retrieve the OpenAI API key from environment variables
api_key = os.getenv('OPENAI_API_KEY')
logger.info(f"OpenAI API key present: {api_key is not None}")

# Assign the API key to the OpenAI library
openai.api_key = api_key

# Global variable to store scraped website content
scraped_data_text = ""

def scrape_website(url: str) -> dict:
    """
    Simple function to scrape a website. 
    Returns a dictionary containing title, headings, and paragraphs.
    """

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Example extraction
        title = soup.title.string if soup.title else "No title found"
        headings = [tag.get_text(strip=True) for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])]
        paragraphs = [p.get_text(strip=True) for p in soup.find_all('p')]

        return {
            "title": title,
            "headings": headings,
            "paragraphs": paragraphs
        }

    except Exception as e:
        return {"error": f"Failed to scrape website: {str(e)}"}

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
        
        # Check for error in scraping
        if "error" in scraped_data:
            logger.error(f"Scraping error: {scraped_data['error']}")
            return jsonify({"error": scraped_data["error"]}), 500

        # Create a text-based representation of the scraped content
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
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are ChatGPT, and this is the scraped content."},
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
