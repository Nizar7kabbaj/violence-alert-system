const PAGE_SIZE = 20; // rows visible per page in the table
let currentPage = 1;
let allAlerts   = [];

function authHeaders() {
  return { 'Authorization': 'Bearer ' + localStorage.getItem('access_token') };
}

function showError(msg) {
  const el = document.getElementById('errorBanner');
  if (!el) return;
  el.textContent = msg;
  el.style.display = 'block';
}

function formatDate(ts) {
  if (!ts) return '—';
  const d = new Date(ts);
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
    + ' ' + d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function renderTable() {
  const tbody = document.getElementById('alertsBody');
  const start = (currentPage - 1) * PAGE_SIZE;
  const slice = allAlerts.slice(start, start + PAGE_SIZE);

  if (slice.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" class="table-empty">No alerts found.</td></tr>';
    return;
  }

  tbody.innerHTML = slice.map(a => `
    <tr>
      <td>${formatDate(a.timestamp)}</td>
      <td>${a.camera_id ?? '—'}</td>
      <td>${a.confidence != null ? (a.confidence * 100).toFixed(1) + '%' : '—'}</td>
      <td><span class="badge ${a.reviewed ? 'badge--yes' : 'badge--no'}">${a.reviewed ? 'Yes' : 'No'}</span></td>
      <td><a class="btn-view" href="alert-detail.html?id=${a.id}">View →</a></td>
    </tr>
  `).join('');
}

function renderPagination() {
  const total     = allAlerts.length;
  const totalPages = Math.ceil(total / PAGE_SIZE);
  const el        = document.getElementById('pagination');

  if (totalPages <= 1) { el.innerHTML = ''; return; }

  el.innerHTML = `
    <button class="btn-page" id="btnPrev" ${currentPage === 1 ? 'disabled' : ''}>← Prev</button>
    <span class="page-info">page ${currentPage} of ${totalPages}</span>
    <button class="btn-page" id="btnNext" ${currentPage === totalPages ? 'disabled' : ''}>Next →</button>
  `;

  document.getElementById('btnPrev').addEventListener('click', () => {
    if (currentPage > 1) { currentPage--; renderTable(); renderPagination(); }
  });

  document.getElementById('btnNext').addEventListener('click', () => {
    if (currentPage < totalPages) { currentPage++; renderTable(); renderPagination(); }
  });
}

async function fetchAllAlerts() {
  const all      = [];
  const pageSize = 100;
  let skip       = 0;

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

    const json = await res.json();
    const page = Array.isArray(json) ? json : (json.items ?? json.data ?? json.alerts ?? []);
    all.push(...page);

    if (page.length < pageSize) break;
    skip += pageSize;
  }

  return all;
}

async function loadAlerts() {
  try {
    allAlerts = await fetchAllAlerts();

    document.getElementById('pageSubtitle').textContent =
      `${allAlerts.length} alert${allAlerts.length !== 1 ? 's' : ''} total`;

    renderTable();
    renderPagination();
  } catch (err) {
    showError('Could not load alerts: ' + err.message);
  }
}

// Guard: only run on alerts page
if (document.getElementById('alertsTable')) {
  const token = localStorage.getItem('access_token');
  if (!token) window.location.href = 'login.html';
  else loadAlerts();
}