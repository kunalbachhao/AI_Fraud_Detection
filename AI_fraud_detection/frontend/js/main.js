const API_URL = "http://127.0.0.1:8000";

const subjectInput = document.getElementById("subject");
const emailContent = document.getElementById("emailContent");
const fileInput = document.getElementById("fileInput");
const fileName = document.getElementById("fileName");
const charCount = document.getElementById("charCount");
const checkBtn = document.getElementById("checkBtn");
const clearBtn = document.getElementById("clearBtn");
const result = document.getElementById("result");
const apiStatus = document.getElementById("apiStatus");

emailContent.addEventListener("input", () => {
  charCount.textContent = emailContent.value.length.toLocaleString();
});

fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];
  if (!file) return;
  fileName.textContent = "Selected: " + file.name;
  if (file.name.toLowerCase().endsWith(".txt")) {
    const reader = new FileReader();
    reader.onload = event => {
      emailContent.value = event.target.result;
      charCount.textContent = emailContent.value.length.toLocaleString();
    };
    reader.readAsText(file);
  }
});

clearBtn.addEventListener("click", () => {
  subjectInput.value = "";
  emailContent.value = "";
  fileInput.value = "";
  fileName.textContent = "";
  charCount.textContent = "0";
  result.className = "card result hidden";
});

async function checkApi() {
  try {
    const response = await fetch(API_URL + "/health");
    const data = await response.json();
    apiStatus.textContent = data.model_loaded ? "API + model ready" : "API online - train model";
    apiStatus.className = "status-pill " + (data.model_loaded ? "ready" : "warning");
  } catch {
    apiStatus.textContent = "API offline";
    apiStatus.className = "status-pill danger";
  }
}

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, char => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
  }[char]));
}

function renderResult(data) {
  const spam = data.prediction === "SPAM";
  const percentage = spam ? data.spam_probability : data.not_spam_probability;
  const indicatorHtml = data.indicators.length
    ? "<ul>" + data.indicators.map(item => "<li>" + escapeHtml(item) + "</li>").join("") + "</ul>"
    : "<p>No common content indicators were detected.</p>";

  result.className = "card result " + (spam ? "spam" : "ham");
  result.innerHTML =
    '<div class="result-top"><div><span class="eyebrow">Prediction</span><h2>' +
    (spam ? "🚨 SPAM" : "✅ NOT SPAM") +
    '</h2></div><div class="score">' + percentage.toFixed(2) + '%</div></div>' +
    '<p class="confidence">Model confidence: ' + data.confidence.toFixed(2) + '%</p>' +
    '<div class="bar"><span style="width:' + Math.min(percentage, 100) + '%"></span></div>' +
    '<div class="probabilities"><span>Spam: <strong>' + data.spam_probability.toFixed(2) +
    '%</strong></span><span>Not spam: <strong>' + data.not_spam_probability.toFixed(2) +
    '%</strong></span></div><div class="indicators"><h3>Content indicators</h3>' +
    indicatorHtml + '</div>';
}

checkBtn.addEventListener("click", async () => {
  const subject = subjectInput.value.trim();
  const body = emailContent.value.trim();
  const file = fileInput.files[0];

  if (!body && !file) {
    result.className = "card result danger";
    result.innerHTML = "<h2>Please enter or upload an email first.</h2>";
    return;
  }

  checkBtn.disabled = true;
  checkBtn.textContent = "Checking...";
  result.className = "card result";
  result.innerHTML = "<p>Analyzing email...</p>";

  try {
    let response;
    if (file && file.name.toLowerCase().endsWith(".eml")) {
      const formData = new FormData();
      formData.append("file", file);
      response = await fetch(API_URL + "/predict-file", { method: "POST", body: formData });
    } else {
      response = await fetch(API_URL + "/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ subject: subject, body: body })
      });
    }

    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Prediction failed.");
    renderResult(data);
  } catch (error) {
    result.className = "card result danger";
    result.innerHTML = "<h2>Could not check the email</h2><p>" + escapeHtml(error.message) + "</p>";
  } finally {
    checkBtn.disabled = false;
    checkBtn.textContent = "Check Email";
  }
});

checkApi();
