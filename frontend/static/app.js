// frontend/static/app.js
const API_BASE = '/api';
let currentUser = null;

async function handleAuth(event, type) {
    event.preventDefault();

    let data;
    if (type === 'login') {
        data = {
            username: document.getElementById('loginUsername').value,
            password: document.getElementById('loginPassword').value
        };
    } else {
        data = {
            username: document.getElementById('signupUsername').value,
            email: document.getElementById('signupEmail').value,
            password: document.getElementById('signupPassword').value
        };
    }

    try {
        const response = await fetch(`${API_BASE}/${type}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
            credentials: 'include'
        });

        const result = await response.json();

        if (response.ok) {
            showToast(`${type === 'login' ? 'Logged in' : 'Signed up'} successfully!`, 'success');
            closeAuthModal();
            await checkAuth();
        } else {
            showToast(result.error, 'error');
        }
    } catch (error) {
        showToast('Network error', 'error');
    }
}

async function logout() {
    try {
        await fetch(`${API_BASE}/logout`, {
            method: 'POST',
            credentials: 'include'
        });
        currentUser = null;
        updateUIForAuth(false);
        showToast('Logged out successfully', 'success');
    } catch (error) {
        showToast('Error logging out', 'error');
    }
}

async function checkAuth() {
    try {
        const response = await fetch(`${API_BASE}/urls`, {
            credentials: 'include'
        });
        if (response.ok) {
            currentUser = true;
            updateUIForAuth(true);
            const urls = await response.json();
            displayUrls(urls);
        } else {
            updateUIForAuth(false);
        }
    } catch (error) {
        updateUIForAuth(false);
    }
}

function updateUIForAuth(isAuthenticated) {
    const navActions = document.getElementById('navActions');
    const userMenu = document.getElementById('userMenu');
    const dashboard = document.getElementById('dashboard');
    const heroSection = document.querySelector('.hero-section');

    if (isAuthenticated) {
        navActions.classList.add('hidden');
        userMenu.classList.remove('hidden');
        dashboard.classList.remove('hidden');
        if (heroSection) heroSection.style.display = 'none';
    } else {
        navActions.classList.remove('hidden');
        userMenu.classList.add('hidden');
        dashboard.classList.add('hidden');
        if (heroSection) heroSection.style.display = 'block';
    }
}

async function shortenUrl(event) {
    event.preventDefault();

    const urlInput = document.getElementById('urlInput');
    const url = urlInput.value.trim();

    if (!url) return;

    try {
        const response = await fetch(`${API_BASE}/shorten`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url }),
            credentials: 'include'
        });

        const result = await response.json();

        if (response.ok) {
            showToast('URL shortened successfully!', 'success');
            urlInput.value = '';
            addUrlToGrid(result);
            updateUrlCount();
        } else {
            showToast(result.error, 'error');
        }
    } catch (error) {
        showToast('Network error', 'error');
    }
}

function addUrlToGrid(urlData) {
    const grid = document.getElementById('urlsGrid');

    const emptyState = grid.querySelector('.empty-state');
    if (emptyState) {
        grid.innerHTML = '';
    }

    const cardHtml = createUrlCard({
        short_code: urlData.short_code,
        short_url: urlData.short_url,
        stats_url: urlData.stats_url,
        original_url: urlData.original_url,
        clicks: 0,
        created_at: new Date().toISOString()
    });

    grid.insertAdjacentHTML('afterbegin', cardHtml);
}

function updateUrlCount() {
    const grid = document.getElementById('urlsGrid');
    const countSpan = document.getElementById('urlCount');
    const cards = grid.querySelectorAll('.url-card');
    countSpan.textContent = `${cards.length}/5`;
}

async function loadUrls() {
    try {
        const response = await fetch(`${API_BASE}/urls`, {
            credentials: 'include'
        });
        if (response.ok) {
            const urls = await response.json();
            displayUrls(urls);
        }
    } catch (error) {
        showToast('Error loading URLs', 'error');
    }
}

function displayUrls(urls) {
    const grid = document.getElementById('urlsGrid');
    const countSpan = document.getElementById('urlCount');

    countSpan.textContent = `${urls.length}/5`;

    if (urls.length === 0) {
        grid.innerHTML = '<div class="empty-state"><p>No links yet. Create your first shortened URL above.</p></div>';
        return;
    }

    grid.innerHTML = urls.map(url => createUrlCard(url)).join('');
}

function createUrlCard(url) {
    const date = new Date(url.created_at).toLocaleDateString();

    return `
        <div class="url-card" data-code="${url.short_code}" onclick="window.location.href='${url.stats_url}'">
            <div class="url-info">
                <div class="url-details">
                    <div class="short-url">
                        <a href="${url.short_url}" target="_blank" onclick="event.stopPropagation()">${url.short_url.replace(/^https?:\/\//, '')}</a>
                        <button class="copy-btn" onclick="event.stopPropagation(); copyToClipboard('${url.short_url}')" title="Copy to clipboard">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                            </svg>
                        </button>
                    </div>
                    <div class="original-url" title="${url.original_url}">
                        ${url.original_url}
                    </div>
                </div>
                <div class="url-stats">
                    <span class="stat" onclick="event.stopPropagation()">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"></circle>
                            <polyline points="12 6 12 12 16 14"></polyline>
                        </svg>
                        ${date}
                    </span>
                    <span class="stat stat-clicks" data-code="${url.short_code}" onclick="event.stopPropagation()">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                            <circle cx="12" cy="12" r="3"></circle>
                        </svg>
                        <span class="clicks-value">${url.clicks}</span> clicks
                    </span>
                    <button class="delete-btn" onclick="event.stopPropagation(); deleteUrl('${url.short_code}')" title="Delete URL">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0h10"></path>
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    `;
}

async function deleteUrl(shortCode) {
    if (!confirm('Are you sure you want to delete this URL?')) return;

    try {
        const response = await fetch(`${API_BASE}/url/${shortCode}`, {
            method: 'DELETE',
            credentials: 'include'
        });

        if (response.ok) {
            showToast('URL deleted successfully', 'success');
            const card = document.querySelector(`.url-card[data-code="${shortCode}"]`);
            if (card) card.remove();
            updateUrlCount();
        } else {
            showToast('Error deleting URL', 'error');
        }
    } catch (error) {
        showToast('Network error', 'error');
    }
}

async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showToast('Copied to clipboard!', 'success');
    } catch (err) {
        showToast('Failed to copy', 'error');
    }
}

function showAuthModal(type) {
    document.getElementById('authModal').classList.remove('hidden');
    switchAuthTab(type);
}

function closeAuthModal() {
    document.getElementById('authModal').classList.add('hidden');
    document.getElementById('loginForm').reset();
    document.getElementById('signupForm').reset();
}

function switchAuthTab(type) {
    const loginTab = document.getElementById('loginTab');
    const signupTab = document.getElementById('signupTab');
    const loginForm = document.getElementById('loginForm');
    const signupForm = document.getElementById('signupForm');

    if (type === 'login') {
        loginTab.classList.add('active');
        signupTab.classList.remove('active');
        loginForm.classList.remove('hidden');
        signupForm.classList.add('hidden');
    } else {
        loginTab.classList.remove('active');
        signupTab.classList.add('active');
        loginForm.classList.add('hidden');
        signupForm.classList.remove('hidden');
    }
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    container.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 10000);
}

document.addEventListener('DOMContentLoaded', () => {
    checkAuth();

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeAuthModal();
        }
    });
});

// Update clicks every 3 seconds
setInterval(async () => {
    if (!currentUser) return;

    const clickElements = document.querySelectorAll('.stat-clicks');
    for (const element of clickElements) {
        const shortCode = element.dataset.code;
        if (shortCode) {
            try {
                const response = await fetch(`${API_BASE}/url/${shortCode}/clicks`, {
                    credentials: 'include'
                });
                if (response.ok) {
                    const data = await response.json();
                    const valueSpan = element.querySelector('.clicks-value');
                    if (valueSpan && valueSpan.textContent !== data.clicks.toString()) {
                        valueSpan.textContent = data.clicks;
                    }
                }
            } catch (error) {
                console.error('Error updating clicks:', error);
            }
        }
    }
}, 10000);