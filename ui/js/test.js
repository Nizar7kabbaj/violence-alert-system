(() => {
  const token = localStorage.getItem('access_token');
  if (!token) { window.location.href = 'login.html'; return; }

  const dropZone   = document.getElementById('dropZone');
  const fileInput  = document.getElementById('fileInput');
  const fileChosen = document.getElementById('fileChosen');
  const fileName   = document.getElementById('fileName');
  const runBtn     = document.getElementById('runBtn');
  const progressWrap = document.getElementById('progressWrap');
  const resultPanel  = document.getElementById('resultPanel');
  const logoutBtn    = document.getElementById('logoutBtn');

  let selectedFile = null;

  // ── logout ──
  logoutBtn.addEventListener('click', () => {
    localStorage.clear();
    window.location.href = 'login.html';
  });

  // ── drag and drop ──
  dropZone.addEventListener('dragover', e => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
  });

  dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-over');
  });

  dropZone.addEventListener('drop', e => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file) setFile(file);
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files[0]) setFile(fileInput.files[0]);
  });

  function setFile(file) {
    selectedFile = file;
    fileName.textContent = file.name;
    fileChosen.style.display = 'block';
    runBtn.disabled = false;
    resultPanel.style.display = 'none';
    resultPanel.className = 'result-panel';
  }

  // ── run detection ──
  runBtn.addEventListener('click', async () => {
    if (!selectedFile) return;

    runBtn.disabled = true;
    progressWrap.style.display = 'block';
    resultPanel.style.display = 'none';

    const form = new FormData();
    form.append('file', selectedFile);
    form.append('camera_id', 'manual-test');

    try {
      const res = await fetch(`${API}/detect`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: form,
      });

      if (res.status === 401) {
        window.location.href = 'login.html';
        return;
      }

      const data = await res.json();

      if (!res.ok) {
        showError(data.detail || 'Detection failed.');
        return;
      }

      showResult(data);

    } catch (err) {
      showError('Could not reach the server.');
    } finally {
      progressWrap.style.display = 'none';
      runBtn.disabled = false;
    }
  });

  function showResult(data) {
    const isViolence = data.label === 'violence';
    const conf = (data.confidence * 100).toFixed(1);

    resultPanel.className = `result-panel ${isViolence ? 'violence' : 'safe'}`;

    document.getElementById('resultVerdict').textContent =
      isViolence ? '⚠ Violence detected' : '✓ No violence detected';

    document.getElementById('resultConfLabel').textContent =
      `confidence: ${conf}%`;

    // snapshot
    const snapshotWrap = document.getElementById('snapshotWrap');
    if (isViolence && data.snapshot_path) {
      snapshotWrap.innerHTML = `
        <div class="result-snapshot">
          <img src="http://localhost:8000/${data.snapshot_path}" alt="Snapshot" />
          <div class="result-snapshot-label">snapshot · frame overlay</div>
        </div>`;
    } else if (isViolence) {
      snapshotWrap.innerHTML = `<div class="result-no-snapshot">no snapshot available</div>`;
    } else {
      snapshotWrap.innerHTML = '';
    }

    // meta rows
    const confClass = isViolence ? 'accent' : 'ok';
    let meta = `
      <div class="meta-row">
        <span class="meta-key">Label</span>
        <span class="meta-val ${confClass}">${data.label}</span>
      </div>
      <div class="meta-row">
        <span class="meta-key">Confidence</span>
        <span class="meta-val ${confClass}">${conf}%</span>
      </div>
      <div class="meta-row">
        <span class="meta-key">Frames sampled</span>
        <span class="meta-val">${data.frame_count}</span>
      </div>
      <div class="meta-row">
        <span class="meta-key">File</span>
        <span class="meta-val">${selectedFile.name}</span>
      </div>`;

    if (isViolence && data.alert_id) {
      meta += `
        <div class="meta-row">
          <span class="meta-key">Alert ID</span>
          <span class="meta-val">${data.alert_id}</span>
        </div>`;
    }

    // confidence meter
    meta += `
      <div class="conf-meter">
        <div class="meta-key">Confidence meter</div>
        <div class="conf-track">
          <div class="conf-fill" style="width:${conf}%"></div>
        </div>
      </div>`;

    document.getElementById('resultMeta').innerHTML = meta;

    // link to alert detail if violence
    if (isViolence && data.alert_id) {
      const link = document.createElement('a');
      link.href = `alert-detail.html?id=${data.alert_id}`;
      link.className = 'alert-link';
      link.textContent = '→ View alert detail';
      document.getElementById('resultMeta').appendChild(link);
    }

    resultPanel.style.display = 'block';
  }

  function showError(msg) {
    resultPanel.className = 'result-panel violence';
    document.getElementById('resultVerdict').textContent = 'Error';
    document.getElementById('resultConfLabel').textContent = '';
    document.getElementById('snapshotWrap').innerHTML = '';
    document.getElementById('resultMeta').innerHTML = `
      <div class="meta-row">
        <span class="meta-key">Detail</span>
        <span class="meta-val accent">${msg}</span>
      </div>`;
    resultPanel.style.display = 'block';
  }
})();