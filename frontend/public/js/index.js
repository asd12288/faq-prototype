/********************************************************************
 * DOM Element References
 ********************************************************************/
const scanBtn = document.getElementById("scanBtn");
const askBtn = document.getElementById("askBtn");
const backBtn = document.getElementById("backBtn");
const askBtneExample = document.getElementById("askBtn-example");

// Sections & Inputs
const scraperUrl = document.getElementById("scraperUrl");
const fileInput = document.getElementById("fileInput");
const queryInput = document.getElementById("query");
const fileNameDisplay = document.getElementById("fileName");
const queryExample = document.getElementById("query-example");

// Response Containers
const faqContainer = document.getElementById("faq");
const responseContainer = document.getElementById("response");
const responseExampleContainer = document.getElementById("response-example");

const step = document.getElementById("step");

/********************************************************************
 * html Template
 ********************************************************************/

function createFaqHtml(data) {
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
  return faqHtml;
}

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

function handleBtnText(input, btn, text) {
  input.addEventListener("input", () => {
    if (input.value.startsWith("http") || input.files.length > 0) {
      btn.innerText = text;
    }
  });
}

/********************************************************************
 * Unified Scan Logic
 ********************************************************************/
async function handleScan() {
  const url = scraperUrl.value.trim();
  const file = fileInput.files[0];

  if (!url && !file) {
    fileNameDisplay.innerText = "אנא הזינו כתובת אתר או העלו קובץ לפני הסריקה";
    return;
  }

  if (url && !url.startsWith("http")) {
    fileNameDisplay.innerText =
      "אנא הזינו כתובת אתר מלאה כולל (http:// או https://)";

    return;
  } else {
    fileNameDisplay.innerText = "";
  }

  // If file exists, upload; otherwise, scrape the given

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

    const html = createFaqHtml(data);

    faqContainer.innerHTML = html;
    toggleStep("step1");
    toggleStep("step2");
    backBtn.classList.remove("hidden");
    step.scrollIntoView({ behavior: "smooth" });
    step.innerText = "שלב 2: שאלו כל שאלה על העסק";
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
      faqContainer.innerHTML = `<div class="error">Error: ${data.error}</div>`;
      return;
    }

    // Build HTML for file analysis & related FAQs
    const html = createFaqHtml(data);

    faqContainer.innerHTML = html;

    toggleStep("step1");
    toggleStep("step2");
    backBtn.classList.remove("hidden");
  } catch (error) {
    faqContainer.innerHTML = `<div class="error">Error: ${error}</div>`;
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

async function handleAskExample() {
  const query = queryExample.value.trim();
  if (!query) {
    alert("הכניסו שאלה לפני לחיצה על הכפתור");
    return;
  }
  loader(responseExampleContainer);
  try {
    const res = await fetch("/ask-us", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: query }),
    });
    const data = await res.json();

    if (data.error) {
      responseExampleContainer.innerHTML = `<div class="error">Error: ${data.error}</div>`;
      return;
    }

    // Build HTML for the main answer
    const mainAnswerHtml = `
      <h2 class="response-title">${query}</h2>
      <p>${data.main_answer}</p>
    `;
    responseExampleContainer.innerHTML = mainAnswerHtml;
  } catch (error) {
    responseExampleContainer.innerHTML = `<div class="error">Error: ${error}</div>`;
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
  backBtn.classList.add("hidden");
}

/********************************************************************
 * Event Listeners
 ********************************************************************/
// Single “Scan” button for both URL & file
scanBtn.addEventListener("click", handleScan);
askBtn.addEventListener("click", handleAsk);
backBtn.addEventListener("click", handleBack);

askBtneExample.addEventListener("click", handleAskExample);

handleBtnText(scraperUrl, scanBtn, "סרוק אתר");
handleBtnText(fileInput, scanBtn, "סרוק קובץ");

// scroll to top
document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
  anchor.addEventListener("click", function (e) {
    e.preventDefault();

    document.querySelector(this.getAttribute("href")).scrollIntoView({
      behavior: "smooth", // Enables smooth scrolling
    });
  });
});
