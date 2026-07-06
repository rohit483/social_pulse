// Store data globally to handle downloads
let currentScrapeData = [];
let currentRawScrapeData = [];
let currentUploadData = [];

// --- Helper: Extract shortcode from Instagram URL or shortcode string
function extractShortcode(input) {
    if (!input) return input;
    const regex = /instagram\.com\/(?:p|reel|reels)\/([a-zA-Z0-9_-]+)/;
    const match = input.match(regex);
    return match ? match[1] : input.trim();
}

// --- Helper: Escape HTML to prevent XSS
function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// --- Helper: Update Sentiment Summary
function updateSummary(elementId, counts) {
    const container = document.getElementById(elementId);
    container.innerHTML = '';
    for (const [sentiment, count] of Object.entries(counts)) {
        const div = document.createElement('div');
        div.className = `badge ${escapeHtml(sentiment.toLowerCase())}`;
        div.innerHTML = `<strong>${escapeHtml(sentiment)}:</strong> ${escapeHtml(String(count))}`;
        container.appendChild(div);
    }
}

// --- Helper: Populate Table (safe from XSS - uses textContent not innerHTML for data)
function populateTable(tableId, data) {
    const tbody = document.querySelector(`#${tableId} tbody`);
    tbody.innerHTML = '';
    data.forEach(item => {
        const row = document.createElement('tr');

        const usernameCell = document.createElement('td');
        usernameCell.textContent = item.username || '';

        const commentCell = document.createElement('td');
        commentCell.textContent = item.comment || '';

        const sentimentCell = document.createElement('td');
        const sentiment = item.sentiment || 'N/A';
        const tag = document.createElement('span');
        tag.className = `tag ${sentiment.toLowerCase()}`;
        tag.textContent = sentiment;
        sentimentCell.appendChild(tag);

        row.appendChild(usernameCell);
        row.appendChild(commentCell);
        row.appendChild(sentimentCell);
        tbody.appendChild(row);
    });
}

// --- Helper: Download Trigger
async function triggerDownload(url, payload) {
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            const contentDisp = response.headers.get('Content-Disposition');
            let filename = contentDisp ? contentDisp.split('filename=')[1] : 'download.csv';
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(downloadUrl);
        } else {
            const err = await response.json();
            alert("Download failed: " + (err.error || "Unknown error"));
        }
    } catch (e) {
        alert("Download error: " + e);
    }
}

// --- 1. Scraper Logic
document.getElementById('scrape-form').addEventListener('submit', async function (e) {
    e.preventDefault();
    const input = document.getElementById('post-url').value;
    const shortcode = extractShortcode(input);

    const loading = document.getElementById('loading');
    const errorMsg = document.getElementById('error-message');
    const resultsSection = document.getElementById('scraper-results-section');

    loading.style.display = 'block';
    errorMsg.style.display = 'none';
    resultsSection.style.display = 'none';

    try {
        const response = await fetch('/scrape', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ shortcode: shortcode })
        });

        const data = await response.json();

        if (response.ok) {
            currentScrapeData = data.analyzed_comments;
            currentRawScrapeData = data.comments;
            updateSummary('scrape-sentiment-summary', data.sentiment_counts);
            populateTable('scrape-results-table', currentScrapeData);
            resultsSection.style.display = 'block';
        } else {
            errorMsg.textContent = data.error || "An error occurred.";
            errorMsg.style.display = 'block';
        }
    } catch (err) {
        errorMsg.textContent = "Network or Server Error.";
        errorMsg.style.display = 'block';
    } finally {
        loading.style.display = 'none';
    }
});

// --- Scraper Downloads
document.getElementById('download-scrape-raw').addEventListener('click', () => {
    const shortcode = extractShortcode(document.getElementById('post-url').value);
    triggerDownload('/download_csv', { comments: currentRawScrapeData, shortcode: shortcode });
});

document.getElementById('download-scrape-analyzed').addEventListener('click', () => {
    triggerDownload('/download_analyzed_csv', { comments: currentScrapeData, filename_prefix: 'Analyzed_Instagram_Comments' });
});

// --- 2. Upload Logic
document.getElementById('upload-form').addEventListener('submit', async function (e) {
    e.preventDefault();
    const fileInput = document.getElementById('csv-file');
    if (fileInput.files.length === 0) return;

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    const loading = document.getElementById('upload-loading');
    const errorMsg = document.getElementById('upload-error');
    const resultsSection = document.getElementById('upload-results-section');

    loading.style.display = 'block';
    errorMsg.style.display = 'none';
    resultsSection.style.display = 'none';

    try {
        const response = await fetch('/analyze_upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        if (response.ok) {
            currentUploadData = data.comments;
            updateSummary('upload-sentiment-summary', data.counts);
            populateTable('upload-results-table', currentUploadData);
            resultsSection.style.display = 'block';
        } else {
            errorMsg.textContent = data.error || "Analysis failed.";
            errorMsg.style.display = 'block';
        }
    } catch (err) {
        errorMsg.textContent = "Upload failed: " + err;
        errorMsg.style.display = 'block';
    } finally {
        loading.style.display = 'none';
    }
});

document.getElementById('download-upload-analyzed').addEventListener('click', () => {
    triggerDownload('/download_analyzed_csv', { comments: currentUploadData, filename_prefix: 'Analyzed_Custom_Upload' });
});
