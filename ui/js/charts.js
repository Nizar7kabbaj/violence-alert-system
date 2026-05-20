function authHeaders() {
  return { 'Authorization': 'Bearer ' + localStorage.getItem('access_token') };
}

function showError(msg) {
  const el = document.getElementById('errorBanner');
  if (!el) return;
  el.textContent = msg;
  el.style.display = 'block';
}

async function fetchAlerts() {
  const allAlerts = [];
  const pageSize  = 100;
  let skip        = 0;

  while (true) {
    const res = await fetch(`${API}/alerts?skip=${skip}&limit=${pageSize}`, {
      headers: authHeaders()
    });

    if (res.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      window.location.href = 'login.html';
      return [];
    }

    if (!res.ok) throw new Error(`Server error ${res.status}`);

    const json    = await res.json();
    const page    = Array.isArray(json) ? json : (json.items ?? json.data ?? json.alerts ?? []);
    allAlerts.push(...page);

    if (page.length < pageSize) break; // last page
    skip += pageSize;
  }

  return allAlerts;
}

function last7Days() {
  const days = [];
  for (let i = 6; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    days.push(d.toISOString().slice(0, 10));
  }
  return days;
}

function formatLabel(iso) {
  const d = new Date(iso + 'T00:00:00');
  return d.toLocaleDateString('en-GB', { month: 'short', day: 'numeric' });
}

function buildChart(countsByDay, labels) {
  const ctx = document.getElementById('alertsChart').getContext('2d');
  const counts = labels.map(d => countsByDay[d] || 0);

  new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels.map(formatLabel),
      datasets: [{
        label: 'Alerts',
        data: counts,
        borderColor: '#e63946',
        backgroundColor: 'rgba(230,57,70,0.07)',
        borderWidth: 2,
        pointRadius: 4,
        pointBackgroundColor: '#e63946',
        pointBorderColor: '#0a0a0c',
        pointBorderWidth: 2,
        tension: 0.3,
        fill: true
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#111114',
          borderColor: '#1e1e24',
          borderWidth: 1,
          titleColor: '#e8e8f0',
          bodyColor: '#6b6b80',
          titleFont: { family: "'Share Tech Mono', monospace", size: 12 },
          bodyFont:  { family: "'Share Tech Mono', monospace", size: 11 },
          callbacks: {
            title: items => items[0].label,
            label: item => `${item.raw} alert${item.raw !== 1 ? 's' : ''}`
          }
        }
      },
      scales: {
        x: {
          grid: { color: '#1e1e24' },
          ticks: { color: '#6b6b80', font: { family: "'Share Tech Mono', monospace", size: 11 } },
          border: { color: '#1e1e24' }
        },
        y: {
          grid: { color: '#1e1e24' },
          ticks: { color: '#6b6b80', font: { family: "'Share Tech Mono', monospace", size: 11 }, stepSize: 1, precision: 0 },
          border: { color: '#1e1e24' },
          min: 0
        }
      }
    }
  });
}

async function loadDashboard() {
  try {
    const alerts = await fetchAlerts();

    const todayStr = new Date().toISOString().slice(0, 10);
    const today    = alerts.filter(a => (a.timestamp || '').slice(0, 10) === todayStr).length;
    const reviewed = alerts.filter(a => a.reviewed).length;

    document.getElementById('statTotal').textContent    = alerts.length;
    document.getElementById('statToday').textContent    = today;
    document.getElementById('statReviewed').textContent = reviewed;

    const labels = last7Days();
    const countsByDay = {};
    alerts.forEach(a => {
      const day = (a.timestamp || '').slice(0, 10);
      if (labels.includes(day)) countsByDay[day] = (countsByDay[day] || 0) + 1;
    });

    buildChart(countsByDay, labels);

    const now = new Date();
    document.getElementById('lastUpdated').textContent =
      'last updated ' + now.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });

  } catch (err) {
    showError('Could not load alerts: ' + err.message);
  }
}

// Logout button (present on all pages)
const btnLogout = document.getElementById('btnLogout');
if (btnLogout) {
  btnLogout.addEventListener('click', () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = 'login.html';
  });
}

// Only run dashboard logic on the dashboard page
if (document.getElementById('alertsChart')) {
  loadDashboard();
}