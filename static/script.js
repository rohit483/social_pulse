document.addEventListener('DOMContentLoaded', () => {
    const urlInput = document.getElementById('instaUrl');
    const scrapeBtn = document.getElementById('scrapeBtn');
    const downloadBtn = document.getElementById('downloadBtn');
    const loadingMsg = document.getElementById('loadingMsg');
    const successMsg = document.getElementById('successMsg');
    const errorMsg = document.getElementById('errorMsg');

    const BACKEND_URL = 'http://127.0.0.1:5001';

    let commentsData = []; // To store fetched comments
    let currentShortcode = ''; // To store the shortcode for the filename

    const extractShortcode = (url) => {
        if (!url || typeof url !== 'string') {
            return null;
        }
        const regex = /(?:https?:\/\/)?(?:www\.)?instagram\.com\/(?:p|reel|reels)\/([a-zA-Z0-9_-]+)\/?/;
        const match = url.trim().match(regex);
        return match ? match[1] : null;
    };

    const convertToCSV = (comments) => {
        const header = 'Username,Comment\n';
        const rows = comments
          .map(c => {
             const username = c.username ? c.username.replace(/"/g, '""') : '';
             const commentText = c.comment ? c.comment.replace(/"/g, '""') : '';
             const escapedUsername = `"${username}"`;
             const escapedComment = `"${commentText}"`;
             return `${escapedUsername},${escapedComment}`;
            })
          .join('\n');
        return header + rows;
    };

    const showStatus = (type, message) => {
        loadingMsg.classList.add('hidden');
        successMsg.classList.add('hidden');
        errorMsg.classList.add('hidden');
        downloadBtn.classList.add('hidden');
        downloadBtn.disabled = true;
        scrapeBtn.disabled = false;

        if (type === 'loading') {
            loadingMsg.textContent = message || 'Loading...';
            loadingMsg.classList.remove('hidden');
            scrapeBtn.disabled = true;
        } else if (type === 'success') {
            successMsg.textContent = message;
            successMsg.classList.remove('hidden');
            if (commentsData.length > 0) {
                downloadBtn.classList.remove('hidden');
                downloadBtn.disabled = false;
                downloadBtn.querySelector('svg').style.display = 'inline-block';
                downloadBtn.childNodes[downloadBtn.childNodes.length - 1].nodeValue = ` Download CSV (${commentsData.length})`;
            }
        } else if (type === 'error') {
            errorMsg.textContent = message;
            errorMsg.classList.remove('hidden');
        }
    };

    scrapeBtn.addEventListener('click', async () => {
        const url = urlInput.value;
        commentsData = [];
        currentShortcode = '';
        showStatus('loading', 'Extracting shortcode...');

        const shortcode = extractShortcode(url);
        currentShortcode = shortcode;

        if (!shortcode) {
            showStatus('error', 'Invalid Instagram URL. Please use a URL like https://www.instagram.com/p/SHORTCODE/');
            return;
        }

        showStatus('loading', `Scraping comments for ${shortcode}...`);

        scrapeBtn.disabled = true;

        try {
            const response = await fetch(`${BACKEND_URL}/scrape`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ shortcode }),
            });

            let result;
            try {
                result = await response.json();
            } catch (e) {
                throw new Error('Invalid JSON response from the server.');
            }

            if (!response.ok) {
                throw new Error(result.error || `Server error: ${response.status} ${response.statusText}`);
            }

            commentsData = result;

            if (commentsData.length === 0) {
                showStatus('success', 'Scraping complete. No comments found.');
            } else {
                showStatus('success', `Successfully scraped ${commentsData.length} comments.`);
            }

        } catch (e) {
            console.error("Scraping failed:", e);
            let errorMessage = `Failed to scrape comments. ${e.message || 'Unknown error'}.`;
            if (e.message && e.message.includes('Failed to fetch')) {
                errorMessage += ` Is the backend server running at ${BACKEND_URL} and accessible? Check CORS configuration on the backend if domains differ.`;
            }
            if (e.message && e.message.includes('401')) {
                errorMessage = 'Failed to scrape comments. Login is required to access comments of this post. Please ensure the backend is logged in.';
            }
            showStatus('error', errorMessage);
        } finally {
            scrapeBtn.disabled = false;
        }
    });

    downloadBtn.addEventListener('click', () => {
        if (!commentsData || commentsData.length === 0) {
            showStatus('error', 'No comment data available to download.');
            return;
        }
        if (!currentShortcode) {
            currentShortcode = 'instagram_post';
        }

        showStatus('loading', 'Generating CSV...');

        try {
            const csvData = convertToCSV(commentsData);
            const blob = new Blob([csvData], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            const blobUrl = URL.createObjectURL(blob);

            link.href = blobUrl;
            link.setAttribute('download', `instagram_comments_${currentShortcode}.csv`);
            document.body.appendChild(link);
            link.click();

            document.body.removeChild(link);
            URL.revokeObjectURL(blobUrl);

            showStatus('success', `Successfully scraped ${commentsData.length} comments. CSV download initiated.`);

        } catch (e) {
             console.error("CSV Generation/Download failed:", e);
             showStatus('error', `Failed to generate or download CSV: ${e.message}`);
        }
    });

    scrapeBtn.disabled = !urlInput.value.trim();
    urlInput.addEventListener('input', () => {
        scrapeBtn.disabled = !urlInput.value.trim();
        if (urlInput.value.trim()) {
             showStatus('clear');
        }
    });
});
