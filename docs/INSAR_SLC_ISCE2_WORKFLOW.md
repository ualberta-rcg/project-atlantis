# Full InSAR displacement: SLC download + ISCE2

This corresponds to the `insar_displacement` scan type in `config/scan.json` (disabled by default).

## Steps

### 1. Find SLC products

Query the CDSE Catalogue for SLC products covering the tile bbox:

```bash
curl -H "Authorization: Bearer $TOKEN" \
  'https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=
    Collection/Name%20eq%20%27SENTINEL-1%27%20and
    Attributes/OData.CSC.StringAttribute/any(i0:i0/Name%20eq%20%27productType%27%20and%20i0/Value%20eq%20%27IW_SLC__1S%27)%20and
    ContentDate/Start%20ge%202023-01-01T00:00:00Z%20and
    ContentDate/Start%20le%202023-01-31T23:59:59Z%20and
    Online%20eq%20true&$top=5'
```

Pick two dates (e.g. 12 days apart for good coherence, or longer for displacement).

### 2. Download SLC to scratch

Download SAFE zips via CDSE OData product download API with your token. Store in scratch (not committed).

### 3. Run ISCE2

```bash
module load isce2/2.6.3
# Reference SLC + secondary SLC -> coregister -> interferogram -> unwrap -> geocode
# Output: displacement (mm LOS), coherence
```

ISCE2 topsStack workflow handles Sentinel-1 TOPS coregistration automatically.

### 4. Use in pipeline

Geocode output to the same grid as stack.tif (GDAL). The `insar_displacement` scan type reads the displacement raster, thresholds persistent displacement, and writes candidates to `results/<tile_id>/insar_displacement/`.

## When to use

Enable only for tiles with high-confidence candidates from the 12 default scan types. Full SLC processing is ~30 min/tile and requires large downloads. Use the GRD-based pipeline as the screener first.
