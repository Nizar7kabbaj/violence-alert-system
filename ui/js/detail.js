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

function fill(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value ?? '—';
}

async function loadAlert(alertId) {
  const res = await fetch(`${API}/alerts/${alertId}`, {
    headers: authHeaders()
  });

  if (res.status === 401) {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = 'login.html';
    return;
  }

  if (res.status === 404) throw new Error('Alert not found.');
  if (!res.ok) throw new Error(`Server error ${res.status}`);

  return res.json();
}

async function markReviewed(alertId) {
  const btn = document.getElementById('btnReview');
  btn.disabled = true;
  btn.textContent = 'Saving...';

  const res = await fetch(`${API}/alerts/${alertId}/review`, {
    method: 'PATCH',
    headers: authHeaders()
  });

  if (res.status === 401) {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = 'login.html';
    return;
  }

  if (!res.ok) throw new Error(`Server error ${res.status}`);

  // 204 = success, no body
  btn.style.display = 'none';
  document.getElementById('reviewSuccess').style.display = 'block';
  document.getElementById('dReviewed').textContent = 'Yes';
}

async function init() {
  const token = localStorage.getItem('access_token');
  if (!token) { window.location.href = 'login.html'; return; }

  const params  = new URLSearchParams(window.location.search);
  const alertId = params.get('id');

  if (!alertId) {
    showError('No alert ID in URL.');
    return;
  }

  document.getElementById('alertId').textContent = 'id: ' + alertId;

  try {
    const alert = await loadAlert(alertId);

    fill('dId',         alert.id ?? alert._id);
    fill('dLabel',      alert.label);
    fill('dConfidence', alert.confidence != null ? (alert.confidence * 100).toFixed(1) + '%' : null);
    fill('dCamera',     alert.camera_id);
    fill('dTimestamp',  formatDate(alert.timestamp));
    fill('dReviewed',   alert.reviewed ? 'Yes' : 'No');
    fill('dReviewedBy', alert.reviewed_by);
    fill('dReviewedAt', formatDate(alert.reviewed_at));

    if (!alert.reviewed) {
      const btn = document.getElementById('btnReview');
      btn.style.display = 'block';
      btn.addEventListener('click', () => markReviewed(alert.id ?? alert._id));
    } else {
      document.getElementById('reviewSuccess').style.display = 'block';
    }

  } catch (err) {
    showError(err.message);
  }
}

// Guard: only run on detail page
if (document.getElementById('detailGrid')) {
  init();
}