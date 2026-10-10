# Smart Safe Nav Frontend

This directory contains the React, Vite, and Leaflet client for Smart Safe Nav.

For complete project setup, backend installation, API endpoints, troubleshooting, and the end-to-end run flow, see the root [README.md](../README.md).

## Quick Start

```powershell
npm install
Copy-Item .env.example .env.local
npm run dev
```

The frontend expects the Flask backend at `http://127.0.0.1:5000` by default. Set `VITE_API_BASE_URL` in `.env.local` when the backend runs elsewhere.

## Commands

```powershell
npm run dev
npm run build
npm run preview
npm run lint
```
