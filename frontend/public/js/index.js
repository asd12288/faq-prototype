/********************************************************************
 * DOM Element References
 ********************************************************************/
const scanBtn = document.getElementById("scanBtn");
const askBtn = document.getElementById("askBtn");
const backBtn = document.getElementById("backBtn");

// Sections & Inputs
const scraperUrl = document.getElementById("scraperUrl");
const fileInput = document.getElementById("fileInput");
const queryInput = document.getElementById("query");
const fileNameDisplay = document.getElementById("fileName");


// Response Containers
const faqContainer = document.getElementById("faq");
const responseContainer = document.getElementById("response");

/********************************************************************
 * Utility Functions
 ********************************************************************/
const toggleStep = (el) => {
  document.getElementById(el).classList.toggle("hidden");
};

const loader = (el) => {
  el.innerHTML = `
    <div class="loading">
      <div class="loader"></div>
    </div>
  `;
};

function resetForm() {
  scraperUrl.value = "";
  fileInput.value = "";
  queryInput.value = "";
  faqContainer.innerHTML = "";
  responseContainer.innerHTML = "";
}

fileInput.addEventListener("change", function () {
  if (fileInput.files.length > 0) {
    fileNameDisplay.textContent = `Selected file: ${fileInput.files[0].name}`;
  } else {
    fileNameDisplay.textContent = "";
  }
});
/********************************************************************
 * Unified Scan Logic
 ********************************************************************/
async function handleScan() {
  const url = scraperUrl.value.trim();
  const file = fileInput.files[0];

  if (!url && !file) {
    alert("אנא הזינו כתובת אתר או העלו קובץ לפני הסריקה");
    return;
  }

  // If file exists, upload; otherwise, scrape the given URL
  if (file) {
    await handleFileUpload(file);
  } else {
    await handleScrape(url);
  }
}

/********************************************************************
 * Scrape Logic
 ********************************************************************/
async function handleScrape(url) {
  loader(faqContainer);

  try {
    const res = await fetch("/scrape", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    const data = await res.json();

    if (data.error) {
      faqContainer.innerHTML = `<div class="error">Error: ${data.error}</div>`;
      return;
    }

    // Build FAQ HTML
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
    faqContainer.innerHTML = faqHtml;
    toggleStep("step1");
    toggleStep("step2");

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
          if (ans && ans.classList.contains("faq-answer")) {
            ans.style.display = "block";
          }
        }
      });
    });
  } catch (error) {
    faqContainer.innerHTML = `<div class="error">Error: ${error}</div>`;
    console.error(error);
  }
}

/********************************************************************
 * File Upload Logic
 ********************************************************************/
async function handleFileUpload(file) {
  const formData = new FormData();
  formData.append("file", file);

  loader(faqContainer);

  try {
    const res = await fetch("/file-upload", {
      method: "POST",
      body: formData,
    });
    const data = await res.json();

    if (data.error) {
      responseContainer.innerHTML = `<div class="error">Error: ${data.error}</div>`;
      return;
    }

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

    responseContainer.innerHTML = faqHtml;
    toggleStep("step1");
    toggleStep("step2");
  } catch (error) {
    responseContainer.innerHTML = `<div class="error">Error: ${error}</div>`;
    console.error(error);
  }
}

/********************************************************************
 * Question-Asking Logic
 ********************************************************************/
async function handleAsk() {
  const query = queryInput.value.trim();
  if (!query) {
    alert("הכניסו שאלה לפני לחיצה על הכפתור");
    return;
  }

  loader(responseContainer);

  try {
    const res = await fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: query }),
    });
    const data = await res.json();

    if (data.error) {
      responseContainer.innerHTML = `<div class="error">Error: ${data.error}</div>`;
      return;
    }

    // Build HTML for the main answer
    const mainAnswerHtml = `
      <h2 class="response-title">${query}</h2>
      <p>${data.main_answer}</p>
    `;
    responseContainer.innerHTML = mainAnswerHtml;
  } catch (error) {
    responseContainer.innerHTML = `<div class="error">Error: ${error}</div>`;
    console.error(error);
  }
}

/********************************************************************
 * Back Button Logic
 ********************************************************************/
function handleBack() {
  toggleStep("step1");
  toggleStep("step2");
  resetForm();
}

/********************************************************************
 * Event Listeners
 ********************************************************************/
// Single “Scan” button for both URL & file
scanBtn.addEventListener("click", handleScan);
askBtn.addEventListener("click", handleAsk);
backBtn.addEventListener("click", handleBack);
