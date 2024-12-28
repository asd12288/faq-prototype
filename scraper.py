import requests
from bs4 import BeautifulSoup


"""SCRAPER"""
def scrape_website(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    content = {"title": soup.title.string if soup.title else "not Title",
               "headings" : [h.get_text() for h in soup.find_all(['h1', 'h2', 'h3'])],
               "paragraphs" : [p.get_text() for p in soup.find_all('p')],
               }
    return content

data = scrape_website('https://www.barista.co.il/')


scraped_data_text = f"""
Title: {data['title']}

Headings:
{'\n'.join(data['headings'])}

Paragraphs:
{'\n'.join(data['paragraphs'])}
"""

