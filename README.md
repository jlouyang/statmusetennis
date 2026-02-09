## Tennis Stats Platform

Minimal project skeleton. See `Development.md` for the full plan.

### Run locally

Backend (API):
```bash
cd /Users/jeremyouyang/Desktop/projects/statmusetennis
source venv/bin/activate
uvicorn backend.main:app --reload
```

Frontend (Next.js):
```bash
cd /Users/jeremyouyang/Desktop/projects/statmusetennis/frontend
npm run dev
```

Open `http://localhost:3000` to use the simple query UI.

Optional: set `BACKEND_URL` if your API isn't on `http://localhost:8000`.

### LLM parser (Gemini)
Set environment variables:
```bash
export QUERY_PARSER=llm
export LLM_API_KEY="your_gemini_key"
export LLM_MODEL="gemini-2.5-flash"
```

If `LLM_API_KEY` is missing, the parser falls back to the rule-based logic.

### Import data
Run the importer as a package so imports resolve correctly:
```bash
cd /Users/jeremyouyang/Desktop/projects/statmusetennis
python3 -m backend.data.import_data
```

### Render deployment (backend)
Use repo root as the working directory.

Build command:
```bash
pip install -r backend/requirements.txt
```

Start command:
```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

Environment variables (Render):
```bash
# Render has no IPv6. Use Supabase Session mode (host must be pooler.supabase.com, not db.*.supabase.co).
# In Supabase: Project → Connect → "Session mode" → copy the URI (host: aws-0-<region>.pooler.supabase.com).
# Do not use Direct or Transaction mode on Render — both use db.*.supabase.co and will fail with "Network is unreachable".
DATABASE_URL="postgres://..."
LLM_API_KEY="your_gemini_key"
LLM_MODEL="gemini-2.5-flash"
QUERY_PARSER="llm"
```