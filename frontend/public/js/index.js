const toggleStep = (el) => {
  const inputEl = document.getElementById(el);
  inputEl.classList.toggle("hidden");
};

document.getElementById("scrapeBtn").addEventListener("click", async () => {
  const url = document.getElementById("scraperUrl").value;
  const responseElement = document.getElementById("faq");

  if (!url) {
    alert("הכניסו כתובת URL לפני לחיצה על הכפתור");
    return;
  }

  loader(responseElement);

  try {
    const res = await fetch("/scrape", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    const data = await res.json();

    if (data.error) {
      responseElement.innerHTML = `<div class="error">Error: ${data.error}</div>`;
    } else {
      console.log(data.faqs);
      // Build HTML to display 3 relevant FAQs
      const faqHtml = `
  <div class="questions-container">
    <h2 class="faq-title">שאלות נפוצות</h2>
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
    responseElement.innerHTML = `<div class="error">Error: ${data.error}</div>`;
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
    alert("הכניסו שאלה לפני לחיצה על הכפתור");
    return;
  }

  loader(responseElement);

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
          <h2 class="response-title">${query}</h2>
          <p>${data.main_answer}</p>
      `;

    // Append the new answer and related FAQs to the existing content
    responseElement.innerHTML = mainAnswerHtml;
  } catch (error) {
    responseElement.innerHTML = `<div class="error">Error: ${data.error}</div>`;
    console.error(error);
  }
});

const loader = (el) => {
  return (el.innerHTML = `<div class="loading">
            <div class="loader"></div>
          </div>`);
};

// SCROLLING ANIMATION
document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
  anchor.addEventListener("click", function (e) {
    e.preventDefault();

    document.querySelector(this.getAttribute("href")).scrollIntoView({
      behavior: "smooth",
    });
  });
});

// Handle file upload
document
  .getElementById("uploadFileBtn")
  .addEventListener("click", async (e) => {
    e.preventDefault();
    const fileInput = document.getElementById("fileInput");
    const responseElement = document.getElementById("response");
    if (!fileInput.files.length) {
      alert("Please select a file.");
      return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    // Show loader
    loader(responseElement);

    try {
      const res = await fetch("/file-upload", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();

      if (data.error) {
        responseElement.innerHTML = `<div class="error">Error: ${data.error}</div>`;
      } else {
        // Build HTML for file analysis & related FAQs

        const faqHtml = (data.faqs || [])
          .map(
            (faq) => `
          <div class="faq-item">
            <h3 class="faq-question">${faq.question}</h3>
            <p class="faq-answer">${faq.answer}</p>
          </div>
          
        `
          )
          .join("");

        responseElement.innerHTML = faqHtml;
        toggleStep("step1");
        toggleStep("step2");
      }
    } catch (error) {
      responseElement.innerHTML = `<div class="error">Error: ${error}</div>`;
      console.error(error);
    }
  });

document.getElementById("backBtn").addEventListener("click", () => {
  toggleStep("step1");
  toggleStep("step2");
  document.getElementById("response").innerHTML = "";
  document.getElementById("fileInput").value = "";
});
