document.getElementById("scrapeBtn").addEventListener("click", async () => {
  const url = document.getElementById("scraperUrl").value;
  const responseElement = document.getElementById("response");

  if (!url) {
    alert("Please enter a URL.");
    return;
  }

  responseElement.textContent = "Scraping website...";

  try {
    const res = await fetch("/scrape", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    const data = await res.json();

    if (data.error) {
      responseElement.textContent = `Error: ${data.error}`;
    } else {
      console.log(data.faqs);
      // Build HTML to display 3 relevant FAQs
      const faqHtml = `
  <div class="faq-container">
    <h2>Frequently Asked Questions</h2>
    <div class="faq-list">
      ${data.faqs
        .map(
          (faq) => `
        <div class="faq-item">
          <h3 class="faq-question">${faq.question}</h3>
          <p class="faq-answer">${faq.answer}</p>
        </div>
      `
        )
        .join("")}
    </div>
    <p>You can now ask a custom question as well!</p>
  </div>
`;

      responseElement.innerHTML = faqHtml;

      // FAQ toggling
      document.querySelectorAll(".faq-question").forEach((q) => {
        q.addEventListener("click", () => {
          const isActive = q.classList.contains("active");
          document
            .querySelectorAll(".faq-question")
            .forEach((qt) => qt.classList.remove("active"));
          document
            .querySelectorAll(".faq-answer")
            .forEach((a) => (a.style.display = "none"));
          if (!isActive) {
            q.classList.add("active");
            const ans = q.nextElementSibling;
            if (ans && ans.classList.contains("faq-answer"))
              ans.style.display = "block";
          }
        });
      });
    }
  } catch (error) {
    responseElement.textContent = "An error occurred while scraping.";
    console.error(error);
  }
});

/********************************************
 * QUESTION-ASKING LOGIC
 ********************************************/
document.getElementById("askBtn").addEventListener("click", async () => {
  const query = document.getElementById("query").value;
  const responseElement = document.getElementById("response");

  if (!query) {
    alert("Please enter a question.");
    return;
  }

  responseElement.textContent = "Fetching answer...";

  try {
    // POST to your /ask endpoint
    const response = await fetch("/ask", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question: query }),
    });
    const data = await response.json();

    // Build HTML for main answer & related FAQs
    const mainAnswerHtml = `
        <div class="main-answer">
          <h2>Answer:</h2>
          <p>${data.main_answer}</p>
        </div>
      `;
    const faqHtml = data.faqs
      .map(
        (faq) => `
        <div class="faq-item">
          <h3 class="faq-question">${faq.question}</h3>
          <p class="faq-answer">${faq.answer}</p>
        </div>
      `
      )
      .join("");

    // Append the new answer and related FAQs to the existing content
    responseElement.innerHTML += mainAnswerHtml + faqHtml;

    // Accordion-like toggling for .faq-question elements
    document.querySelectorAll(".faq-question").forEach((question) => {
      question.addEventListener("click", () => {
        const isActive = question.classList.contains("active");

        // Close all open FAQ items
        document
          .querySelectorAll(".faq-question")
          .forEach((q) => q.classList.remove("active"));
        document
          .querySelectorAll(".faq-answer")
          .forEach((a) => (a.style.display = "none"));

        // If the clicked question was not active, open it
        if (!isActive) {
          question.classList.add("active");
          const answer = question.nextElementSibling;
          if (answer && answer.classList.contains("faq-answer")) {
            answer.style.display = "block";
          }
        }
      });
    });
  } catch (error) {
    responseElement.textContent =
      "An error occurred while fetching the response.";
    console.error(error);
  }
});
