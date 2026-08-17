# PermissionLens — Frontend

React + Vite frontend for PermissionLens, a static Android APK permission and
contextual risk analyzer (SIH prototype).

## What's in this phase

This covers the **complete frontend**: landing page, drag-and-drop APK
upload, a scan/loading state, and the results dashboard (risk stamp,
permission manifest, evidence, plain-language explanation, recommendations).

It runs standalone out of the box using a deterministic local mock analyzer
(`src/lib/mockAnalysis.js`), so it's fully demoable before the backend exists.
Once the FastAPI backend (later phases) is deployed, point `VITE_API_URL` at
it and the app automatically switches from demo mode to real analysis — no
code changes needed.

## Run locally

\`\`\`bash
npm install
npm run dev
\`\`\`

## Connect the real backend later

Copy `.env.example` to `.env.local` and set:

\`\`\`
VITE_API_URL=https://your-backend-url
\`\`\`

The backend is expected to expose `POST /analyze` accepting `multipart/form-data`
with a `file` field, returning JSON shaped like the object in
`src/lib/mockAnalysis.js`'s `analyzeLocally` return value.

## Deploy to Vercel

1. Push this project to a GitHub repo.
2. In Vercel: **New Project → Import** the repo.
3. Framework preset: **Vite**. Build command `npm run build`, output dir `dist` (Vercel detects this automatically).
4. Add `VITE_API_URL` under Project → Settings → Environment Variables once the backend is live.
5. Deploy.

## Project structure

\`\`\`
src/
  components/   UI building blocks (Navbar, Hero, UploadTool, ReportCard, ...)
  lib/          api.js (backend call + fallback), mockAnalysis.js (demo data)
  App.jsx       page composition
  index.css     design tokens + all component styles
\`\`\`