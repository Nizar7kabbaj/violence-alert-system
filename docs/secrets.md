# Secrets Management

All secrets live in a `.env` file at the project root. The file is gitignored. You recreate it on every machine.

The template `.env.example` lists the variable names. This file explains where each value comes from.

## Generating a secret

For anything marked "generate with secrets.token_hex(64)" below, run this from PowerShell inside the active venv:

```powershell
python -c "import secrets; print(secrets.token_hex(64))"
```

That gives you a 128-character hex string (64 bytes of entropy). Run it once per secret. Never reuse the same value across two different variables.

## Variable reference

### MongoDB

| Variable | Source | Notes |
|---|---|---|
| `MONGODB_URI` | Atlas dashboard, Connect, Drivers | Replace `<password>` with the DB user password, not your Atlas account password |
| `MONGODB_DB_NAME` | Fixed: `vas` | Database name inside the cluster |

### JWT

| Variable | Source | Notes |
|---|---|---|
| `JWT_SECRET` | `secrets.token_hex(64)` | Signs access tokens |
| `JWT_REFRESH_SECRET` | `secrets.token_hex(64)` | Signs refresh tokens. Must differ from `JWT_SECRET` |
| `JWT_ACCESS_MIN` | Fixed: `15` | Access token TTL in minutes |
| `JWT_REFRESH_DAYS` | Fixed: `7` | Refresh token TTL in days |

### Telegram

| Variable | Source | Notes |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Created via @BotFather in Telegram | Format: `<numeric-id>:<35-char alphanumeric>` |
| `TELEGRAM_CHAT_ID` | The `getUpdates` API after you send a first message to the bot | Numeric. Negative for groups |

### Runtime

| Variable | Source | Notes |
|---|---|---|
| `ENVIRONMENT` | `development` locally, `production` in Docker | Drives log format and error verbosity |

### Rate limiting

| Variable | Source | Notes |
|---|---|---|
| `RATE_LIMIT_LOGIN` | Default: `5/minute` | Format: `<count>/<period>`. See slowapi docs |

### Detection

| Variable | Source | Notes |
|---|---|---|
| `DETECTION_THRESHOLD` | Default: `0.85` | Probability above which a frame counts as violent |

### Service-to-service auth

| Variable | Source | Notes |
|---|---|---|
| `INTERNAL_API_KEY` | `secrets.token_hex(64)` | Header `X-Internal-API-Key` for watcher to backend writes |

### CORS

| Variable | Source | Notes |
|---|---|---|
| `CORS_ALLOWED_ORIGINS` | Comma-separated list | Example: `http://localhost:8080,http://127.0.0.1:8080` |

### Observability

| Variable | Source | Notes |
|---|---|---|
| `METRICS_ALLOWED_IPS` | Comma-separated list of IPs | Restricts access to the `/metrics` endpoint |

## Rules

1. Don't commit `.env`. It's in `.gitignore`. Check before every commit:

```powershell
   git status --ignored
```

2. If a secret ever lands in a public commit, treat it as compromised. Regenerate it. Restart every service that uses it.

3. `JWT_SECRET` and `JWT_REFRESH_SECRET` must hold different values. If you reuse one, someone who steals an access token can forge a refresh token and vice versa.

4. Production runs differently. There, secrets come from a vault like AWS Secrets Manager or HashiCorp Vault, not a `.env` file. This project runs locally only. Vault integration belongs to a later phase.