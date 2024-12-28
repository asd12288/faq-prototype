"""OPENAI QUESTIONS FILL"""
from openai import OpenAI
from scraper import scraped_data_text

with open('prompt.txt', 'r', encoding = 'utf-8') as f:
    prompt = f.read()


client = OpenAI()

completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": scraped_data_text},
        {
            "role": "user",
            "content": prompt,
        }
    ]
)

file_name = 'faq.html'
with open(file_name, 'w', encoding='utf-8') as f:
    f.write(completion.choices[0].message.content)

print(f"the FAQ SECTION HAS BEEN WRITE {file_name}")