// frontend/static/stats.js
const API_BASE = '/api';
const shortCode = window.location.pathname.split('/').pop();

let currentUrl = null;

let chart = null;

async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/url/${shortCode}/stats`, {
            credentials: 'include'
        });
        
        if (response.status === 401) {
            window.location.href = '/';
            return;
        }
        
        const data = await response.json();
        currentUrl = data.url;
        displayStats(data);
        loadUrlSettings();
    } catch (error) {
        showToast('Error loading statistics', 'error');
    }
}

async function loadUrlSettings() {
    try {
        const response = await fetch(`${API_BASE}/url/${shortCode}/settings`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            populateCountries(data.blocked_countries || []);
            document.getElementById('maxClicks').value = data.max_clicks || '';
            if (data.expires_at) {
                document.getElementById('expiresAt').value = data.expires_at.slice(0, 16);
            }
        } else {
            populateCountries([]);
        }
    } catch (error) {
        populateCountries([]);
    }
}

function populateCountries(selectedCodes = []) {
    const select = document.getElementById('blockedCountries');
    if (!select) return;
    
    const countries = [
        { code: 'US', name: 'United States' },
        { code: 'GB', name: 'United Kingdom' },
        { code: 'CA', name: 'Canada' },
        { code: 'AU', name: 'Australia' },
        { code: 'DE', name: 'Germany' },
        { code: 'FR', name: 'France' },
        { code: 'ES', name: 'Spain' },
        { code: 'IT', name: 'Italy' },
        { code: 'NL', name: 'Netherlands' },
        { code: 'RU', name: 'Russia' },
        { code: 'CN', name: 'China' },
        { code: 'JP', name: 'Japan' },
        { code: 'KR', name: 'South Korea' },
        { code: 'IN', name: 'India' },
        { code: 'BR', name: 'Brazil' }
    ];
    
    select.innerHTML = countries.map(c => `
        <option value="${c.code}" ${selectedCodes.includes(c.code) ? 'selected' : ''}>
            ${c.name} (${c.code})
        </option>
    `).join('');
}

async function saveSettings() {
    const settings = {
        blocked_countries: Array.from(document.getElementById('blockedCountries').selectedOptions).map(o => o.value),
        max_clicks: document.getElementById('maxClicks').value ? parseInt(document.getElementById('maxClicks').value) : null,
        expires_at: document.getElementById('expiresAt').value || null
    };
    
    try {
        const response = await fetch(`${API_BASE}/url/${shortCode}/settings`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings),
            credentials: 'include'
        });
        
        if (response.ok) {
            showToast('Settings saved successfully', 'success');
        } else {
            showToast('Error saving settings', 'error');
        }
    } catch (error) {
        showToast('Error saving settings', 'error');
    }
}

function displayStats(data) {
    document.getElementById('shortCode').textContent = data.url.short_code;
    document.getElementById('totalClicks').textContent = data.stats.total_clicks;
    document.getElementById('todayClicks').textContent = data.stats.today_clicks;
    document.getElementById('weekClicks').textContent = data.stats.week_clicks;
    document.getElementById('uniqueCountries').textContent = data.stats.unique_countries;
    
    updateChart(data.timeline);
    updateCountriesList(data.countries);
    updateRecentClicks(data.recent_clicks);
}

function updateChart(timeline) {
    const ctx = document.getElementById('clicksChart').getContext('2d');
    
    if (chart) {
        chart.destroy();
    }
    
    if (!timeline || timeline.length === 0) {
        ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
        ctx.font = '14px Inter';
        ctx.fillStyle = '#a0a0a0';
        ctx.textAlign = 'center';
        ctx.fillText('No data yet', ctx.canvas.width/2, ctx.canvas.height/2);
        return;
    }
    
    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: timeline.map(t => t.date),
            datasets: [{
                label: 'Clicks',
                data: timeline.map(t => t.clicks),
                borderColor: '#0066ff',
                backgroundColor: 'rgba(0, 102, 255, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#fff' }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: '#2a2a2a' },
                    ticks: { color: '#a0a0a0' }
                },
                x: {
                    grid: { color: '#2a2a2a' },
                    ticks: { color: '#a0a0a0' }
                }
            }
        }
    });
}

function updateCountriesList(countries) {
    const list = document.getElementById('countriesList');
    
    if (!countries || countries.length === 0) {
        list.innerHTML = '<div class="empty-state">No data yet</div>';
        return;
    }
    
    list.innerHTML = countries.map(c => `
        <div class="country-item">
            <span class="country-flag">${getFlagEmoji(c.country)}</span>
            <span class="country-name">${c.country || 'Unknown'}</span>
            <span class="country-count">${c.count} clicks</span>
            <span class="country-percentage">${(c.percentage || 0).toFixed(1)}%</span>
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${c.percentage || 0}%"></div>
            </div>
        </div>
    `).join('');
}

function updateRecentClicks(clicks) {
    const container = document.getElementById('recentClicks');
    
    if (!clicks || clicks.length === 0) {
        container.innerHTML = '<div class="empty-state">No clicks yet</div>';
        return;
    }
    
    container.innerHTML = clicks.map(c => `
        <div class="click-row">
            <div class="click-info">
                <span class="click-time">${new Date(c.clicked_at).toLocaleString()}</span>
                <span class="click-location">
                    ${getFlagEmoji(c.country)} ${c.city || 'Unknown'}, ${c.country || 'Unknown'}
                </span>
            </div>
            <div class="click-details">
                <span class="click-device">${c.device_type || 'Unknown'} • ${c.os || 'Unknown'} • ${c.browser || 'Unknown'}</span>
                <span class="click-ip">${c.ip_address}</span>
            </div>
        </div>
    `).join('');
}

function getFlagEmoji(countryCode) {
    if (!countryCode || countryCode === 'UN' || countryCode === 'Unknown') return '🌍';
    const codePoints = countryCode
        .toUpperCase()
        .split('')
        .map(char => 127397 + char.charCodeAt());
    return String.fromCodePoint(...codePoints);
}

function visitUrl() {
    if (currentUrl?.short_url) {
        window.open(currentUrl.short_url, '_blank');
    } else {
        showToast('URL not available', 'error');
    }
}

function showToast(message, type) {
    const container = document.getElementById('toastContainer') || createToastContainer();
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 10000);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container';
    document.body.appendChild(container);
    return container;
}

function copyStatsUrl() {
    const url = window.location.href;
    navigator.clipboard.writeText(url);
    showToast('Stats URL copied!', 'success');
}

document.addEventListener('DOMContentLoaded', loadStats);
setInterval(loadStats, 10000);