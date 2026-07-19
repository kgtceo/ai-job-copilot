# Deploy

Two pieces: the **FastAPI backend** (Railway) and the **Next.js frontend** (Vercel).
The frontend calls the backend, so deploy the backend first and wire its URL into
the frontend.

> Both deploy from the GitHub repo, so push to GitHub first.

## 1. Backend → Railway

1. Railway → **New Project → Deploy from GitHub repo** → pick `ai-job-copilot`.
2. The repo has a **`Dockerfile`**, so Railway builds with Docker — it installs the
   package + deps and runs `python -m uvicorn job_copilot.api:app` on `$PORT`.
   Nothing to configure. (We use Docker because Railway's auto-detection builder
   didn't reliably install the deps.)
3. **Variables** (Settings → Variables):
   - `ANTHROPIC_API_KEY` = your key (this is how the key reaches prod — NOT the
     gitignored `.env`).
   - `COPILOT_CORS_ORIGINS` = your Vercel URL, e.g. `https://ai-job-copilot.vercel.app`
     (add your custom domain too if you use one, comma-separated). Localhost is
     always allowed via regex, so dev keeps working.
4. **Expose it:** Settings → **Networking → Generate Domain** → gives a public URL
   like `https://ai-job-copilot-production.up.railway.app` (Railway shows
   "Unexposed service" until you do this).
5. Check `GET /health` → `{"ok":true,"configured":true}`. `configured:false` means
   the API key variable isn't set.

## 2. Frontend → Vercel

1. Vercel → **Add New → Project** → import `ai-job-copilot`, set **Root Directory =
   `web`** (the Next app lives there).
2. **Environment Variables**:
   - `NEXT_PUBLIC_API_URL` = the Railway backend URL from step 1.4.
3. Deploy. Vercel gives `https://ai-job-copilot.vercel.app` (or attach a custom
   subdomain, e.g. `jobcopilot.kareemghazal.com`).
4. Back on Railway, make sure `COPILOT_CORS_ORIGINS` includes the exact Vercel URL.

## 3. Verify
Open the Vercel URL → **Load example** → **Analyse**. First call takes ~10–30s
(four sequential Claude calls). Then the two PDF download buttons should work too.

## Notes
- The pipeline runs 10–30s, which exceeds serverless free-function timeouts — hence
  a persistent backend (Railway) rather than Vercel functions.
- No system fonts / `.ttf` needed for PDFs (standard-14 Helvetica), so nothing
  extra to install on Railway.
