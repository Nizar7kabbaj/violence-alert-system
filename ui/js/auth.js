const API = 'http://localhost:8000/api/v1';

const loginBtn = document.getElementById('loginBtn');

if (loginBtn) {
  loginBtn.addEventListener('click', async () => {
    const email    = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const err      = document.getElementById('errorMsg');

    err.style.display = 'none';

    if (!email || !password) {
      err.textContent = 'Email and password are required.';
      err.style.display = 'block';
      return;
    }

    loginBtn.disabled = true;
    loginBtn.textContent = 'Authenticating...';

    try {
      const res = await fetch(`${API}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Login failed.');
      }

      const data = await res.json();
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      window.location.href = 'dashboard.html';

    } catch (e) {
      err.textContent = e.message;
      err.style.display = 'block';
      loginBtn.disabled = false;
      loginBtn.textContent = 'Login';
    }
  });

  document.addEventListener('keydown', e => {
    if (e.key === 'Enter') loginBtn.click();
  });
}