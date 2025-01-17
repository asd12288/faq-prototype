(function () {
  const BASE_URL = "https://faq-prototype.onrender.com";

  function loadFaqWidget(elementId, options = {}) {
    const container = document.getElementById(elementId);
    if (!container) {
      console.error("Element not found");
      return;
    }

    // Create an iframe for isolation
    const iframe = document.createElement("iframe");
    iframe.style.width = "100%";
    iframe.style.height = "400px"; // Adjust based on your design
    iframe.style.border = "none";
    container.appendChild(iframe);

    // Inject the widget's content into the iframe
    const doc = iframe.contentWindow.document;
    doc.open();
    doc.write(`
        <!DOCTYPE html>
        <html lang="en">
        <head>
          <link rel="stylesheet" href="${BASE_URL}/styles.css" />
        </head>
        <body>
          <div id="faq-widget">
            <!-- Your component will render here -->
          </div>
          <script src="${BASE_URL}/bundle.js"></script>
          <script>
            // Initialize the component
            new FaqWidget("#faq-widget", ${JSON.stringify(options)});
          </script>
        </body>
        </html>
      `);
    doc.close();
  }

  // Expose to global scope
  window.loadFaqWidget = loadFaqWidget;
})();
