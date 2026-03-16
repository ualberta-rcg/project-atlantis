# Full InSAR displacement: SLC download + ISCE2

This is the path to **real displacement in mm** (line-of-sight) when the ground shifts. Use it when you want “time displacement” in the InSAR sense.

## Steps

### 1. Find SLC products

- **Catalogue:** `https://catalogue.dataspace.copernicus.eu/odata/v1/Products`
- **Filter:** Collection `SENTINEL-1`, productType `IW_SLC__1S`, footprint intersects your bbox (WKT polygon), `ContentDate` in range, `Online eq true`.
- **Output:** Product `Name` (e.g. `S1A_IW_SLC__1SDV_20230101T...SAFE`) and download URL from `Assets`.
- Pick **two dates** (e.g. 12 days apart for good coherence, or longer for displacement).

Example (replace bbox and dates):

```bash
# Get token first (same as Process API or ODP)
# Then (one line, split for readability):
curl -H "Authorization: Bearer $TOKEN" \
  'https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=
    Collection/Name%20eq%20%27SENTINEL-1%27%20and
    Attributes/OData.CSC.StringAttribute/any(i0:i0/Name%20eq%20%27productType%27%20and%20i0/Value%20eq%20%27IW_SLC__1S%27)%20and
    ContentDate/Start%20ge%202023-01-01T00:00:00Z%20and
    ContentDate/Start%20le%202023-01-31T23:59:59Z%20and
    Online%20eq%20true&$top=5'
```

### 2. Download SLC to $SCRATCH

- Use the product download API (see CDSE OData product download docs) with your token. Download the SAFE zip to e.g. `$SCRATCH/insar/<site_id>/`.
- You need **two** SLCs (reference + secondary).

### 3. Run ISCE2 on the cluster

- **Module:** `module load isce2/2.6.3` (CVMFS).
- **Workflow:** Sentinel-1 TOPS InSAR. ISCE2 has a **topsStack** (or similar) workflow: reference SLC + secondary SLC → coregister → interferogram → (optional) unwrap → geocode → displacement/coherence.
- **Paths:** If the cluster’s isce2 does not expose the stack by default, set:
  - `ISCE_STACK` to the path of `contrib/stack` inside the ISCE2 install,
  - and add `topsStack` to `PATH` (see ISCE2 docs / GitHub).
- **Output:** Geocoded interferogram, coherence, and (if unwrapped) displacement in mm. Use the displacement raster as an extra “chance” or “displacement_mm” layer in the pipeline.

### 4. Use displacement in the pipeline

- Geocode to the same grid as your variance stack (e.g. with GDAL), then:
  - **Option A:** Displacement magnitude (or gradient) as a second score — combine with variance-based chance (e.g. `chance = 0.6 * var_chance + 0.4 * disp_chance`).
  - **Option B:** Export displacement and coherence as extra rasters in `results/<site_id>/` (e.g. `displacement_los.tif`, `coherence.tif`) so archaeologists can overlay “where the ground moved.”

## References

- CDSE OData: product search and download.
- ISCE2: [https://github.com/isce-framework/isce2](https://github.com/isce-framework/isce2), `contrib/stack/topsStack`, README.
- Your cluster: `SENTINEL_FLATTEN_COREGISTER.md` (isce2/2.6.3 for InSAR).
