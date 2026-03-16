# Services and environment variables

**Full table:** See the plan document **section 5g** (Services and env vars).

Summary:

- **CDSE Process API (OAuth):** `CDSE_CLIENT_ID`, `CDSE_CLIENT_SECRET` — from CDSE dashboard → OAuth clients. Used by `fetch_s1_site.py`, `request_sentinel1_cdse.py`.
- **CDSE On-Demand (coherence):** Same as above or `CDSE_USERNAME` / `CDSE_PASSWORD` for ODP. Used by `order_coh12.py`.
- **CDSE Catalogue / OData:** Same token as Process API. Used for SLC search/download (Path B InSAR).

No secret values are stored in the repo; set these in your environment (e.g. `~/.env` or cluster env).
