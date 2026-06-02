// Cybersecurity Dashboard - Main JavaScript

// 1. CONFIGURATION
const API_URL = 'http://127.0.0.1:8000';

document.addEventListener('DOMContentLoaded', function() {
    initUrlChecker();
    initEmailScanner();
});

// -------------------------------------------------------------------------
// URL CHECKER (Connects to /scan-url)
// -------------------------------------------------------------------------
function initUrlChecker() {
    const scanBtn = document.getElementById('scanUrlBtn');
    const results = document.getElementById('urlResults');
    const urlInputEl = document.getElementById('urlInput');
    
    if (scanBtn && results && urlInputEl) {
        scanBtn.addEventListener('click', async function() {
            const urlInput = urlInputEl.value.trim();
            
            if (!urlInput) {
                alert("Please enter a URL");
                return;
            }
            
            // UI Loading
            results.innerHTML = '<p>🔍 Scanning...</p>';
            results.classList.remove('hidden');
            scanBtn.disabled = true;
            
            try {
                // FETCH FROM PYTHON BACKEND
                const response = await fetch(`${API_URL}/scan-url`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: urlInput })
                });

                if (!response.ok) throw new Error('Backend error');

                const data = await response.json();

                // CHECK RESULT (Python sends "safe" or "phishing")
                const isSafe = data.prediction === 'safe';
                
                // RENDER HTML
                results.innerHTML = `
                    <div style="padding: 15px; border-radius: 8px; background-color: ${isSafe ? '#dcfce7' : '#fee2e2'}; border: 1px solid ${isSafe ? '#22c55e' : '#ef4444'};">
                        <h3 style="color: ${isSafe ? '#15803d' : '#b91c1c'}; margin-top:0;">
                            ${isSafe ? '✅ Safe URL' : '🚫 Phishing Detected'}
                        </h3>
                        <p><strong>URL:</strong> ${data.url}</p>
                        <p><strong>Confidence:</strong> ${data.confidence_score}%</p>
                        <p>${isSafe ? "This website appears safe to visit." : "Warning! This website shows malicious behavior."}</p>
                    </div>
                `;

            } catch (error) {
                console.error(error);
                results.innerHTML = `<p style="color: red;">⚠️ Error connecting to server. Is backend running?</p>`;
            } finally {
                scanBtn.disabled = false;
            }
        });
    }
}

// -------------------------------------------------------------------------
// EMAIL SCANNER (Connects to /predict)
// -------------------------------------------------------------------------
function initEmailScanner() {
    const scanBtn = document.getElementById('scanEmailBtn');
    const results = document.getElementById('emailResults');
    const fileInput = document.getElementById('emailFileInput');
    const fileLabel = document.getElementById('emailFileLabel');
    const clearBtn = document.getElementById('clearFileBtn');
    const emailTextarea = document.getElementById('emailContent');

    if (scanBtn && fileInput) {

        // A. HANDLE FILE SELECTION (UI Logic)
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                // 1. Update Label
                fileLabel.textContent = "📄 " + file.name;
                fileLabel.style.color = "#00ed64"; // Green accent
                
                // 2. Show Clear Button
                if(clearBtn) clearBtn.style.display = 'inline-block';

                // 3. Read file content into Textarea (So user can see it)
                const reader = new FileReader();
                reader.onload = function(e) {
                    emailTextarea.value = e.target.result;
                };
                reader.readAsText(file);
            }
        });

        // B. HANDLE CLEAR BUTTON
        if(clearBtn) {
            clearBtn.addEventListener('click', function() {
                fileInput.value = ''; // Reset input
                emailTextarea.value = ''; // Clear text box
                fileLabel.textContent = "Choose .eml or .txt file";
                fileLabel.style.color = "#94a3b8"; // Reset color
                this.style.display = 'none'; // Hide clear button
            });
        }

        // C. HANDLE SCAN BUTTON (Backend Logic)
        scanBtn.addEventListener('click', async function () {
            // Check if there is content
            const textContent = emailTextarea.value.trim();
            const file = fileInput.files[0];

            if (!textContent && !file) {
                alert("Please paste email content or upload a file first.");
                return;
            }

            // UI Loading
            if(results) {
                results.innerHTML = "Analyzing Email..."; 
                results.classList.remove('hidden');
                scanBtn.disabled = true;
                scanBtn.innerHTML = "Scanning...";
            }
            
            const formData = new FormData();

            // LOGIC: If a real file is selected, send that. 
            // If only text is pasted, convert text to a Blob (fake file) to send to backend.
            if (file) {
                formData.append('file', file);
            } else {
                const blob = new Blob([textContent], { type: 'text/plain' });
                formData.append('file', blob, 'pasted-email.txt');
            }

            try {
                const response = await fetch(`${API_URL}/predict`, {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) throw new Error('Backend error');

                const data = await response.json();
                
                // Assuming backend returns: { "prediction": "Safe", "confidence": 95 }
                const isSafe = data.prediction === 'Safe';
                
                results.innerHTML = `
                   <div style="padding: 15px; border-radius: 8px; background-color: ${isSafe ? '#dcfce7' : '#fee2e2'}; border: 1px solid ${isSafe ? '#22c55e' : '#ef4444'};">
                        <h3 style="color: ${isSafe ? '#15803d' : '#b91c1c'}; margin-top:0;">
                            Result: ${data.prediction}
                        </h3>
                        <p><strong>Confidence Score:</strong> ${data.confidence}%</p>
                        <p>${isSafe ? "No phishing patterns detected." : "⚠️ Suspicious content found in this email."}</p>
                    </div>
                `;
            } catch (e) {
                console.error(e);
                if(results) results.innerHTML = `<p style="color:red">Error connecting to server. Is the backend running?</p>`;
            } finally {
                scanBtn.disabled = false;
                scanBtn.innerHTML = `
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                    <polyline points="7 10 12 15 17 10"/>
                    <line x1="12" y1="15" x2="12" y2="3"/>
                </svg> Scan Email`;
            }
        });
    }
}