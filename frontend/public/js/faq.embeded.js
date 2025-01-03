(async function () {
    const faqContainer = document.createElement('div');
    faqContainer.id = 'faq-container';
    faqContainer.innerHTML = '<div style="text-align: center; margin: 1em;">Loading FAQs...</div>';
    document.body.appendChild(faqContainer);
  
    const styles = `
      #faq-container { margin: 2em; font-family: Arial, sans-serif; }
      .faq-title { font-size: 1.5em; font-weight: bold; margin-bottom: 1em; }
      .faq-item { margin: 1em 0; }
      .faq-question { cursor: pointer; color: #007BFF; }
      .faq-answer { display: none; margin-left: 1em; }
    `;
    const styleTag = document.createElement('style');
    styleTag.innerHTML = styles;
    document.head.appendChild(styleTag);
  
    try {
      // Update the fetch URL to point to your deployed /scrape endpoint
      const res = await fetch('https://faq-prototype.onrender.com/scrape', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: window.location.origin }),
      });
      const data = await res.json();
  
      if (data.error) {
        faqContainer.innerHTML = `<div style="color: red;">Error: ${data.error}</div>`;
      } else {
        const faqHtml = `
          <div class="faq-title">Frequently Asked Questions</div>
          ${data.faqs
            .map(
              (faq) => `
                <div class="faq-item">
                  <div class="faq-question">${faq.question}</div>
                  <div class="faq-answer">${faq.answer}</div>
                </div>
              `
            )
            .join('')}
        `;
        faqContainer.innerHTML = faqHtml;
  
        document.querySelectorAll('.faq-question').forEach((q) => {
          q.addEventListener('click', () => {
            const answer = q.nextElementSibling;
            answer.style.display = answer.style.display === 'block' ? 'none' : 'block';
          });
        });
      }
    } catch (error) {
      faqContainer.innerHTML = `<div style="color: red;">An unexpected error occurred: ${error.message}</div>`;
    }
  })();
  