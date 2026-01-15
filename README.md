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

