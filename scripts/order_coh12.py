#!/usr/bin/env python3
"""
Order CARD-COH12 (Sentinel-1 coherence, 12-day pair) from CDSE On-Demand Processing.
Finds one SLC over the site bbox, submits the order, polls until done, downloads result.
Use: CDSE_USERNAME + CDSE_PASSWORD (or CDSE_CLIENT_ID + CDSE_CLIENT_SECRET for token).
Output: coherence product (zip) in results/<site_id>/raw/ or --out-dir.
"""
import os
import sys
import time
import json
import argparse
import urllib.parse

import requests

# CDSE ODP and Catalogue
ODP_BASE = "https://odp.dataspace.copernicus.eu/odata/v1"
CATALOGUE_BASE = "https://catalogue.dataspace.copernicus.eu/odata/v1"
TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"

# Workflow name for coherence 12-day pair
WORKFLOW_COH12 = "card_coh12_public"


def get_token():
    """Prefer client credentials; fallback to password."""
    client_id = os.environ.get("CDSE_CLIENT_ID", "").strip()
    client_secret = os.environ.get("CDSE_CLIENT_SECRET", "").strip()
    if client_id and client_secret:
        r = requests.post(
            TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
    else:
        user = os.environ.get("CDSE_USERNAME", "").strip()
        pw = os.environ.get("CDSE_PASSWORD", "").strip()
        if not user or not pw:
            print("Set CDSE_CLIENT_ID+CDSE_CLIENT_SECRET or CDSE_USERNAME+CDSE_PASSWORD", file=sys.stderr)
            sys.exit(1)
        r = requests.post(
            TOKEN_URL,
            data={"grant_type": "password", "client_id": "cdse-public", "username": user, "password": pw},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
    r.raise_for_status()
    return r.json()["access_token"]


def bbox_to_polygon_wkt(bbox):
    """bbox [min_lon, min_lat, max_lon, max_lat] -> WKT POLYGON for OData."""
    min_lon, min_lat, max_lon, max_lat = bbox
    return f"POLYGON(({min_lon} {min_lat},{max_lon} {min_lat},{max_lon} {max_lat},{min_lon} {max_lat},{min_lon} {min_lat}))"


def search_slc(token, bbox, start_date, end_date):
    """Return one SLC product ID that intersects bbox and is in date range."""
    poly = bbox_to_polygon_wkt(bbox)
    # OData filter: SENTINEL-1, IW SLC, footprint intersects, date, online
    filters = [
        "Collection/Name eq 'SENTINEL-1'",
        "Attributes/OData.CSC.StringAttribute/any(i0:i0/Name eq 'productType' and (i0/Value eq 'IW_SLC__1S' or i0/Value eq 'SLC'))",
        f"OData.CSC.Intersects(Footprint=geography'SRID=4326;{poly}')",
        f"ContentDate/Start ge {start_date}T00:00:00.000Z",
        f"ContentDate/Start le {end_date}T23:59:59.999Z",
        "Online eq true",
    ]
    filt = " and ".join(f"({f})" for f in filters)
    url = f"{CATALOGUE_BASE}/Products?$filter={urllib.parse.quote(filt)}&$top=1&$orderby=ContentDate/Start desc"
    r = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=60)
    r.raise_for_status()
    data = r.json()
    if not data.get("value"):
        return None
    return data["value"][0].get("Name")  # product ID e.g. S1A_IW_SLC__1SDV_...SAFE


def submit_coh12_order(token, slc_reference, name="arch_coh12"):
    """Submit CARD-COH12 order. Returns order ID."""
    payload = {
        "WorkflowName": WORKFLOW_COH12,
        "InputProductReference": {"Reference": slc_reference},
        "Priority": 1,
        "Name": name,
    }
    r = requests.post(
        f"{ODP_BASE}/ProductionOrder/OData.CSC.Order",
        json=payload,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        timeout=30,
    )
    if r.status_code not in (200, 201):
        print(r.status_code, r.text, file=sys.stderr)
        r.raise_for_status()
    out = r.json()
    order = out.get("value", out)
    return order.get("Id"), order.get("Status")


def poll_order(token, order_id, max_wait_sec=3600, poll_sec=30):
    """Poll until completed or failed. Returns status."""
    start = time.time()
    while time.time() - start < max_wait_sec:
        r = requests.get(
            f"{ODP_BASE}/ProductionOrders({order_id})",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        status = data.get("Status", "").lower()
        msg = data.get("StatusMessage", "")
        print(f"  Status: {status} — {msg}")
        if status == "completed":
            return "completed"
        if status == "failed":
            return "failed"
        time.sleep(poll_sec)
    return "timeout"


def download_product(token, order_id, out_path):
    """Download order result to out_path."""
    r = requests.get(
        f"{ODP_BASE}/ProductionOrder({order_id})/Product/$value",
        headers={"Authorization": f"Bearer {token}"},
        timeout=120,
        stream=True,
    )
    r.raise_for_status()
    with open(out_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"Downloaded: {out_path}")


def main():
    ap = argparse.ArgumentParser(description="Order CARD-COH12 coherence for a site")
    ap.add_argument("site_id", help="Site key (e.g. qubbet_el_hawa)")
    ap.add_argument("--start", default="2023-01-01", help="Start date for SLC search")
    ap.add_argument("--end", default="2023-01-31", help="End date for SLC search")
    ap.add_argument("--out-dir", default=None, help="Output dir (default: results/<site_id>/raw)")
    ap.add_argument("--no-download", action="store_true", help="Only submit order, do not poll/download")
    args = ap.parse_args()

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from sites import SITES
    if args.site_id not in SITES:
        print(f"Unknown site: {args.site_id}", file=sys.stderr)
        sys.exit(1)
    bbox = SITES[args.site_id]["bbox"]

    token = get_token()
    print("Searching for SLC over bbox...")
    slc_id = search_slc(token, bbox, args.start, args.end)
    if not slc_id:
        print("No SLC found for this bbox and date range.", file=sys.stderr)
        sys.exit(1)
    print(f"Found: {slc_id}")

    print("Submitting CARD-COH12 order...")
    order_id, status = submit_coh12_order(token, slc_id, name=f"arch_coh12_{args.site_id}")
    print(f"Order ID: {order_id}")

    if args.no_download:
        print("Use ODP API to check status and download when completed.")
        return

    print("Polling until completed...")
    final = poll_order(token, order_id)
    if final != "completed":
        print(f"Order ended with: {final}", file=sys.stderr)
        sys.exit(1)

    out_dir = args.out_dir or os.path.join(os.path.dirname(__file__), "..", "results", args.site_id, "raw")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"coh12_{args.site_id}_{args.start}_to_{args.end}.zip")
    download_product(token, order_id, out_path)
    print("Done. Unzip and use coherence layer (e.g. low coherence = change) in detection.")


if __name__ == "__main__":
    main()
