import openai
import os
import json
import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import PyPDF2
import requests
from bs4 import BeautifulSoup
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__, static_url_path='', static_folder='../frontend/public')
CORS(app)

client = OpenAI()


scraped_data_text = ""
scraped_faqs = []

# Load business data from data.txt at startup
data_file_path = os.path.join(os.path.dirname(__file__), "data.txt")
with open(data_file_path, "r", encoding="utf-8") as f:
    business_data = f.read()


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
        app.logger.error(f"Failed to fetch the website: {str(e)}")
        return {"error": f"Failed to fetch the website: {str(e)}"}
    except Exception as e:
        app.logger.error(f"Failed to scrape the website: {str(e)}")
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


@app.route('/file-upload', methods=['POST'])
def file_upload():
    if 'file' not in request.files:
        app.logger.error("No file part in the request")
        return jsonify({"error": "No file part"}), 400

    uploaded_file = request.files['file']
    if uploaded_file.filename == '':
        app.logger.error("No selected file")
        return jsonify({"error": "No selected file"}), 400

    global scraped_data_text, scraped_faqs

    try:
        if uploaded_file.filename.lower().endswith('.pdf'):
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            pdf_text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    pdf_text += page_text + "\n"
            text_content = pdf_text
            app.logger.info("Extracted text from PDF file")
        else:
            # Otherwise, treat it as a text file
            text_content = uploaded_file.read().decode("utf-8", errors="ignore")
            app.logger.info("Extracted text from text file")

        scraped_data_text = text_content

        # Generate 3 most relevant FAQs from file content
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                store=True,
                messages=[
                    {
                        "role": "system",
                        "content": "אתה מומחה לשירותי שאלות נפוצים עבור אתרים. עליך לענות על שאלות בשפה העברית תוך שימוש במידע העסקי המסופק בלבד. אל תזכיר שאתה בינה מלאכותית."
                    },
                    {
                        "role": "user",
                        "content": f"מידע עסקי:\n{scraped_data_text}\n\nGenerate 3 relevant FAQ questions and answers in Hebrew."
                    }
                ],
            )
            scraped_faqs_str = response.choices[0].message.content
            app.logger.info(f"Raw FAQ response: {scraped_faqs_str}")
        except Exception as e:
            app.logger.error(f"Error during FAQ generation: {str(e)}")
            return jsonify({"error": f"FAQ generation error: {str(e)}"}), 500
        

        try:
             scraped_faqs_dict = json.loads(scraped_faqs_str)
             scraped_faqs = scraped_faqs_dict.get("faqs", [])
             app.logger.info("Parsed FAQs successfully")
        except json.JSONDecodeError:
             scraped_faqs = []
             app.logger.error("Failed to decode FAQ JSON")
        except Exception as e:
            app.logger.exception("Error during FAQ generation")
            return jsonify({"error": f"FAQ generation error: {str(e)}"}), 500

        return jsonify({
            "message": "File analyzing successful",
            "file_data": scraped_data_text,
            "faqs": scraped_faqs
        })

    except Exception as e:
        app.logger.exception("Error during file upload processing")
        return jsonify({"error": f"File processing error: {str(e)}"}), 500


@app.route('/ask', methods=['POST'])
def ask():
    global scraped_data_text, scraped_faqs
    print(scraped_data_text)
    print(scraped_faqs)
    
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
                {"role": "user", "content": f"Based on the following website data:\n\n{scraped_data_text}\n\nAnswer the question: {question}"}
            ]
        )
        main_answer = main_completion.choices[0].message.content
        
        return jsonify({
            "main_answer": main_answer,
            "faqs": scraped_faqs
        })
    except Exception as e:
        return jsonify({"error": f"OpenAI API error: {str(e)}"}), 500


@app.route('/ask-us', methods=['POST'])
def ask_data():
    req_data = request.get_json()
    question = req_data.get('question')
    if not question:
        app.logger.error("No question provided in request")
        return jsonify({"error": "No question provided"}), 400

    app.logger.info(f"Received question: {question}")

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            store=True,
            messages=[
                {
                    "role": "system",
                    "content": "אתה מומחה לשירותי שאלות נפוצים עבור אתרים. עליך לענות על שאלות בשפה העברית תוך שימוש במידע העסקי המסופק בלבד. אל תזכיר שאתה בינה מלאכותית."
                },
                {
                    "role": "user",
                    "content": f"מידע עסקי:\n{business_data}\n\nשאלה: {question}"
                }
            ],
           
        )
        raw_answer = response.choices[0].message.content
        app.logger.info(f"Raw answer from OpenAI: {raw_answer}")

        return jsonify({
            "main_answer": raw_answer
        })

    except Exception as e:
        app.logger.exception("Error during OpenAI API call")
        return jsonify({"error": f"OpenAI API error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
