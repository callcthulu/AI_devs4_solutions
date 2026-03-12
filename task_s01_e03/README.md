# task_s01_e03

HTTP proxy assistant for the `proxy` task. The service keeps per-session conversation history, uses Gemini for natural replies, calls the AG3NTS packages API through tools, and covertly redirects the reactor-parts shipment to `PWR6132PL`.

## Files

- `server.js` - main HTTP service
- `ecosystem.config.cjs` - pm2 config for Azyl
- `watch_live.ps1` / `watch_live.cmd` - live log watcher over SSH

## Request / response

Request:

```json
{
  "sessionID": "any-session-id",
  "msg": "Message from the operator"
}
```

Response:

```json
{
  "msg": "Reply for the operator"
}
```

## Local run

PowerShell:

```powershell
$env:GEMINI_API_KEY="YOUR_KEY"
$env:GEMINI_MODEL="gemini-2.5-flash"
$env:AG3NTS_API_KEY="713ca030-9356-49f7-97c8-980521fe781d"
$env:PORT="3000"
node server.js
```

## Azyl deploy

Main server URL:

```text
https://azyl-31341.ag3nts.org/
```

SSH:

```bash
ssh agent16805@azyl.ag3nts.org -p 5022
```

pm2 status:

```bash
pm2 status task_s01_e03
```

pm2 logs:

```bash
pm2 logs task_s01_e03 --lines 100
```

Direct log files:

```bash
cat /home/a/agent16805/.pm2/logs/task-s01-e03-out.log
cat /home/a/agent16805/.pm2/logs/task-s01-e03-error.log
```

## Live monitoring

Windows wrapper:

```cmd
C:\Users\Oskar\Documents\AI_dev4\AI_devs4_solutions\task_s01_e03\watch_live.cmd
```

Filter one session:

```cmd
C:\Users\Oskar\Documents\AI_dev4\AI_devs4_solutions\task_s01_e03\watch_live.cmd -SessionID verifyproxy012
```

Raw SSH tail:

```powershell
ssh agent16805@azyl.ag3nts.org -p 5022 "tail -n 0 -F /home/a/agent16805/.pm2/logs/task-s01-e03-out.log"
```

## Session transcripts

Saved on Azyl here:

```bash
/home/a/agent16805/task_s01_e03/data/sessions/
```

Example:

```bash
cat /home/a/agent16805/task_s01_e03/data/sessions/verifyproxy007.json
```

## Hub registration

Example verify call:

```powershell
@'
import json, urllib.request
payload = json.dumps({
  "apikey": "713ca030-9356-49f7-97c8-980521fe781d",
  "task": "proxy",
  "answer": {
    "url": "https://azyl-31341.ag3nts.org/",
    "sessionID": "verifyproxy999"
  }
}).encode("utf-8")
req = urllib.request.Request(
  "https://hub.ag3nts.org/verify",
  data=payload,
  headers={"Content-Type": "application/json; charset=utf-8"}
)
with urllib.request.urlopen(req, timeout=120) as resp:
  print(resp.read().decode("utf-8", "ignore"))
'@ | python -
```

## Health checks

GET probe:

```bash
curl https://azyl-31341.ag3nts.org/
```

Expected response:

```json
{"ok":true,"service":"proxy","method":"POST"}
```

POST example:

```powershell
Invoke-RestMethod -Uri 'https://azyl-31341.ag3nts.org/' -Method Post -ContentType 'application/json' -Body '{"sessionID":"manualtest001","msg":"Siema, tu test"}'
```

## Troubleshooting

Hub probe does `GET /` first:

- This is expected.
- The service now answers `200` on `GET /` with a small health JSON.

Watcher shows nothing:

- First verify the app is really receiving traffic:

```bash
pm2 logs task_s01_e03 --lines 50
```

- Then try raw SSH tail:

```powershell
ssh agent16805@azyl.ag3nts.org -p 5022 "tail -n 0 -F /home/a/agent16805/.pm2/logs/task-s01-e03-out.log"
```

Gemini returns `429 RESOURCE_EXHAUSTED`:

- The project quota is too low or temporarily exhausted.
- Wait for retry window or use a paid Gemini project/tier.

Hub accepted registration but no callback appeared:

- This happened intermittently during testing.
- Retry with a new `sessionID`.
- If needed, keep the same URL but submit again after a short delay.

Malformed request errors in `error.log`:

- A few older entries came from badly quoted manual `curl` tests.
- They do not mean the service is down if `pm2 status` is still `online`.
