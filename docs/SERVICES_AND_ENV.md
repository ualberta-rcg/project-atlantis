# Services and environment variables

## Required

| Variable | Source | Used by |
|----------|--------|---------|
| `CDSE_CLIENT_ID` | [CDSE dashboard](https://dataspace.copernicus.eu) -> OAuth clients | `fetch_s1_tile.py`, `order_coh12.py` |
| `CDSE_CLIENT_SECRET` | Same dashboard | Same |
| `REPO_URL` | `git@github.com:ualberta-rcg/project-atlantis.git` | `run_pipeline.py` (clone + push) |
| `GIT_SSH_COMMAND` | `ssh -i ~/.ssh/archaeology-deploy-key -o StrictHostKeyChecking=accept-new` | Git push auth |

## Optional

| Variable | Default | Used by |
|----------|---------|---------|
| `BATCH_SIZE` | 5 | `run_pipeline.py` (tiles per claim) |
| `CLUSTER_ID` | hostname | Logging in process_record.json |
| `SCRATCH_DIR` | `$TMPDIR` | Raw image storage (not committed) |
| `CDSE_USERNAME` | -- | `order_coh12.py` (password fallback) |
| `CDSE_PASSWORD` | -- | `order_coh12.py` (password fallback) |

## CDSE OAuth token flow

```
POST https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token
  grant_type=client_credentials
  client_id=<CDSE_CLIENT_ID>
  client_secret=<CDSE_CLIENT_SECRET>
-> access_token (used as Bearer token for Process API and Catalogue)
```

## SSH deploy key

One ed25519 keypair per repo. Private key at `~/.ssh/archaeology-deploy-key` (never committed). Public key added to GitHub repo Settings -> Deploy keys with write access.

No secret values are stored in the repo. Set them in `~/.bashrc` or cluster environment.
