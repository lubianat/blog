#!/usr/bin/env python3
"""GerBI logo in OMERO.figure, one panel per dot, each panel cropped onto an
isolated nucleus found automatically in an OME-Zarr image.

    pip install "zarr>=3" fsspec aiohttp scikit-image scipy numpy
    python3 make_gerbi_nuclei_figure.py [ZARR_URL] > gerbi_nuclei_figure.json

What it does
  1. Reads the OME-Zarr metadata (axes, datasets, channels, pixel sizes).
  2. Picks the DAPI/DNA/Hoechst channel and segments nuclei on one plane.
  3. Keeps single, well-shaped nuclei that don't touch the edge and ranks
     them by how far they are from the nearest other nucleus.
  4. Uses the best N_CELLS (10-20) as square crops, spread over the 92 dots
     with random rotation/flip, and writes an OMERO.figure (v9) JSON.
Progress and the chosen nuclei are printed to stderr; the JSON to stdout.
"""
import json
import math
import random
import re
import sys

import numpy as np
from scipy import ndimage as ndi
from skimage import filters, measure, morphology

ZARR_URL = "https://livingobjects.ebi.ac.uk/idr/zarr/v0.5/idr0033A/BR00109990_C2.zarr/0"

# ---- nucleus picking ------------------------------------------------------
N_CELLS = 15              # how many distinct nuclei to use (10-20)
DAPI_PATTERN = r"dapi|dna|hoechst|nuc"   # channel label match; falls back to channel 0
SEG_TARGET_SIZE = 1500    # segment on the smallest resolution at least this wide
MIN_SOLIDITY = 0.93       # rejects clumps / touching pairs / blebby shapes
AREA_RANGE = (0.6, 1.8)   # x median nucleus area
CROP_PAD = 1.5            # crop side = PAD x the nucleus' longest bbox side

# ---- look -----------------------------------------------------------------
DOT_COLOR = "0B983A"      # GerBI green (as it should appear on white)
GREY_COLOR = "DADADA"
INVERT = True             # white background; LUT set to complement so colour comes out right
RANDOM_SEED = 42
RANDOMISE_ORIENTATION = True

# ---- logo geometry (logo-image px, measured from the 213x161 px GerBI logo) -
DOTS = [
    (141.2, 26.0), (155.1, 30.9), (136.3, 40.1), (150.0, 45.2),
    (131.1, 54.3), (144.9, 59.3), (126.1, 68.6), (139.9, 73.5), (153.8, 73.1),
    (121.0, 82.2), (134.8, 87.2), (161.0, 85.9),
    (160.5, 101.0), (154.2, 115.0), (150.5, 129.6),
    (97.3, 105.3), (111.5, 110.0), (125.5, 114.4), (139.6, 119.1),
    (115.1, 145.3), (129.2, 145.3), (143.3, 145.3), (157.5, 145.3),
]
INCLUDE_GREY = True
GREY_ORIGIN = (80.99, 20.42)
GREY_V1 = (13.595, 4.901)
GREY_V2 = (-5.061, 14.077)
GREY_BOUNDS = (56, 14, 199, 156)
GREY_CLEARANCE = 9
SCALE = 4
PANEL = 44
MARGIN = 40


def log(*a):
    print(*a, file=sys.stderr)


# --------------------------------------------------------------------------
# OME-Zarr reading
# --------------------------------------------------------------------------
def open_group(url):
    import zarr
    if url.startswith("http"):
        store = zarr.storage.FsspecStore.from_url(url, read_only=True)
    else:
        store = zarr.storage.LocalStore(url, read_only=True)
    return zarr.open_group(store, mode="r")


def read_image(url):
    grp = open_group(url)
    attrs = dict(grp.attrs)
    ome = attrs.get("ome", attrs)            # v0.5 nests under "ome"
    zarr_version = 3 if "ome" in attrs else 2
    ms = ome["multiscales"][0]
    axes = ms.get("axes") or [{"name": n} for n in "tczyx"]
    axes = [a if isinstance(a, dict) else {"name": a} for a in axes]
    names = [a["name"] for a in axes]
    arrays = {}
    for ds in ms["datasets"]:
        arr = grp[ds["path"]]
        arrays[ds["path"]] = {"shape": list(arr.shape), "dtype": str(arr.dtype), "arr": arr}
    return {"ome": ome, "ms": ms, "axes": axes, "names": names, "arrays": arrays,
            "zarr_version": zarr_version, "omero": ome.get("omero", {})}


def pick_dapi(img):
    names = img["names"]
    sizeC = img["arrays"][img["ms"]["datasets"][0]["path"]]["shape"][names.index("c")] if "c" in names else 1
    chs = img["omero"].get("channels") or []
    for i, ch in enumerate(chs):
        if re.search(DAPI_PATTERN, ch.get("label", ""), re.I):
            return i, sizeC
    log("No DAPI-like channel label found; using channel 0")
    return 0, sizeC


def load_plane(img, path, c, z, t):
    arr = img["arrays"][path]["arr"]
    idx = []
    for n in img["names"]:
        idx.append({"c": c, "z": z, "t": t}.get(n, slice(None)))
    return np.asarray(arr[tuple(idx)]).astype(np.float32)


# --------------------------------------------------------------------------
# Nucleus finding
# --------------------------------------------------------------------------
def find_isolated_nuclei(plane):
    sm = filters.gaussian(plane, sigma=1.5, preserve_range=True)
    mask = sm > filters.threshold_otsu(sm)
    mask = ndi.binary_fill_holes(morphology.opening(mask, morphology.disk(2)))
    lab = measure.label(mask)
    props = [p for p in measure.regionprops(lab) if p.area >= 20]
    if not props:
        return [], lab
    med = np.median([p.area for p in props])
    H, W = plane.shape
    cands = []
    for p in props:
        r0, c0, r1, c1 = p.bbox
        if r0 == 0 or c0 == 0 or r1 == H or c1 == W:
            continue                                   # touches image edge
        if not (AREA_RANGE[0] * med <= p.area <= AREA_RANGE[1] * med):
            continue
        if p.solidity < MIN_SOLIDITY:
            continue
        # isolation = distance from this nucleus to the nearest other foreground pixel
        m = int(max(r1 - r0, c1 - c0) * 3)
        R0, C0, R1, C1 = max(0, r0 - m), max(0, c0 - m), min(H, r1 + m), min(W, c1 + m)
        win = lab[R0:R1, C0:C1]
        others = (win > 0) & (win != p.label)
        if others.any():
            d = ndi.distance_transform_edt(~others)
            iso = float(d[win == p.label].min())
        else:
            iso = float(m)                             # nothing nearby within the window
        cands.append({"label": p.label, "cy": p.centroid[0], "cx": p.centroid[1],
                      "size": max(r1 - r0, c1 - c0), "area": p.area,
                      "solidity": p.solidity, "isolation": iso,
                      "mean": float(sm[lab == p.label].mean())})
    # isolation first, nice round shape as tie-break
    cands.sort(key=lambda c: c["isolation"] * c["solidity"], reverse=True)
    return cands, lab


# --------------------------------------------------------------------------
# Figure building
# --------------------------------------------------------------------------
def complement(h):
    return "%06X" % (0xFFFFFF ^ int(h, 16))


def default_colors(n):
    base = ["0000FF", "00FF00", "FF0000", "FF00FF", "00FFFF", "FFFF00", "FFFFFF"]
    return [base[i % len(base)] for i in range(n)]


def pixel_sizes(img):
    ds0 = img["ms"]["datasets"][0]
    scale = next((ct["scale"] for ct in ds0.get("coordinateTransformations", [])
                  if ct["type"] == "scale"), None)
    out = {}
    if scale:
        for dim in "xyz":
            if dim in img["names"]:
                out[dim] = scale[img["names"].index(dim)]
    return out


def zarr_attrs(img):
    a = {"multiscales": [img["ms"]],
         "arrays": {p: {"shape": v["shape"], "dtype": v["dtype"]} for p, v in img["arrays"].items()},
         "zarr_version": img["zarr_version"]}
    if img["ms"].get("version"):
        a["version"] = img["ms"]["version"]
    elif img["zarr_version"] == 3:
        a["version"] = img["ome"].get("version", "0.5")
    if img["omero"]:
        a["omero"] = img["omero"]
    return a


def grey_dots():
    ox, oy = GREY_ORIGIN
    (ax, ay), (bx, by) = GREY_V1, GREY_V2
    xmin, ymin, xmax, ymax = GREY_BOUNDS
    pts = []
    for i in range(-20, 21):
        for j in range(-20, 21):
            x, y = ox + i * ax + j * bx, oy + i * ay + j * by
            if xmin <= x <= xmax and ymin <= y <= ymax and \
                    all(math.hypot(x - gx, y - gy) >= GREY_CLEARANCE for gx, gy in DOTS):
                pts.append((x, y))
    return pts


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else ZARR_URL
    url = url.rstrip("/")
    random.seed(RANDOM_SEED)

    log("Reading", url)
    img = read_image(url)
    names = img["names"]
    path0 = img["ms"]["datasets"][0]["path"]
    shape0 = img["arrays"][path0]["shape"]
    sizeX, sizeY = shape0[-1], shape0[-2]
    sizeZ = shape0[names.index("z")] if "z" in names else 1
    sizeT = shape0[names.index("t")] if "t" in names else 1
    theZ, theT = sizeZ // 2, 0
    dapi, sizeC = pick_dapi(img)
    log(f"Image {sizeX}x{sizeY}, Z={sizeZ}, T={sizeT}, C={sizeC}; DAPI channel = {dapi}")

    # segment on a modest resolution level
    seg_path = path0
    for ds in img["ms"]["datasets"]:
        if img["arrays"][ds["path"]]["shape"][-1] >= SEG_TARGET_SIZE:
            seg_path = ds["path"]
    f = sizeX / img["arrays"][seg_path]["shape"][-1]   # seg px -> full-res px
    plane = load_plane(img, seg_path, dapi, theZ, theT)
    cands, _ = find_isolated_nuclei(plane)
    log(f"{len(cands)} clean single nuclei found; using the {min(N_CELLS, len(cands))} most isolated")
    if not cands:
        sys.exit("No usable nuclei found - try lowering MIN_SOLIDITY or widening AREA_RANGE")
    picks = cands[:N_CELLS]

    # contrast for DAPI: from omero metadata if present, else from the nuclei themselves
    full_lo, full_hi = float(plane.min()), float(plane.max())
    ch_meta = (img["omero"].get("channels") or [{}] * sizeC)
    win = ch_meta[dapi].get("window", {}) if dapi < len(ch_meta) else {}
    bg = float(np.percentile(plane, 5))
    hi = float(np.percentile([c["mean"] for c in picks], 90)) * 1.3
    d_start, d_end = bg, min(hi, win.get("max", full_hi))

    # one view per picked nucleus: crop square around it (OMERO.figure maths:
    # for a square panel, visible side = min(orig_w, orig_h) * 100 / zoom,
    # centred at (orig_w/2 - dx, orig_h/2 - dy))
    views = []
    for c in picks:
        cx, cy, side = c["cx"] * f, c["cy"] * f, c["size"] * f * CROP_PAD
        views.append({"zoom": min(sizeX, sizeY) * 100.0 / side,
                      "dx": sizeX / 2 - cx, "dy": sizeY / 2 - cy})
        log(f"  nucleus at ({cx:.0f}, {cy:.0f}) px  size {c['size']*f:.0f}  "
            f"isolation {c['isolation']*f:.0f} px  solidity {c['solidity']:.2f}")

    psz = pixel_sizes(img)
    zattrs = zarr_attrs(img)
    colors = default_colors(sizeC)
    name = url.split("/")[-2] + "/" + url.split("/")[-1] if url.split("/")[-1].isdigit() else url.split("/")[-1]

    def panel(x, y, color, view):
        chans = []
        for i in range(sizeC):
            m = ch_meta[i] if i < len(ch_meta) else {}
            w = m.get("window", {})
            active = i == dapi
            chans.append({
                "label": m.get("label", f"Ch{i}"), "active": active,
                "color": (complement(color) if INVERT else color) if active else m.get("color", colors[i]),
                "reverseIntensity": INVERT,
                "window": {"min": w.get("min", full_lo), "max": w.get("max", full_hi),
                           "start": d_start if active else w.get("start", full_lo),
                           "end": d_end if active else w.get("end", full_hi)},
            })
        p = {
            "imageId": url, "name": name,
            "x": round(x, 1), "y": round(y, 1), "width": PANEL, "height": PANEL,
            "orig_width": sizeX, "orig_height": sizeY,
            "sizeZ": sizeZ, "theZ": theZ, "sizeT": sizeT, "theT": theT,
            "rdefs": {"model": "-"}, "pixelsType": img["arrays"][path0]["dtype"],
            "zoom": round(view["zoom"], 2), "dx": round(view["dx"], 2), "dy": round(view["dy"], 2),
            "rotation": random.randrange(360) if RANDOMISE_ORIENTATION else 0,
            "horizontal_flip": RANDOMISE_ORIENTATION and random.random() < 0.5,
            "vertical_flip": False,
            "selected": False, "labels": [], "deltaT": [],
            "channels": chans, "zarr": zattrs,
        }
        for dim in "xyz":
            if dim in psz:
                p[f"pixel_size_{dim}"] = psz[dim]
        for dim in "xy":
            if dim in psz:
                p[f"pixel_size_{dim}_unit"] = "MICROMETER"
                p[f"pixel_size_{dim}_symbol"] = "µm"
        return p

    greens = list(DOTS)
    greys = grey_dots() if INCLUDE_GREY else []
    allpts = greens + greys
    x0 = min(p[0] for p in allpts)
    y0 = min(p[1] for p in allpts)

    # every nucleus is used before any repeats; shuffled so neighbours differ
    def view_stream():
        while True:
            vs = views[:]
            random.shuffle(vs)
            yield from vs
    vs = view_stream()
    pos = lambda x, y: (MARGIN + (x - x0) * SCALE, MARGIN + (y - y0) * SCALE)
    panels = [panel(*pos(x, y), GREY_COLOR, next(vs)) for x, y in greys]
    panels += [panel(*pos(x, y), DOT_COLOR, next(vs)) for x, y in greens]

    fig = {
        "version": 9, "figureName": "GerBI logo - nuclei",
        "page_size": "pixels",
        "paper_width": int(MARGIN * 2 + (max(p[0] for p in allpts) - x0) * SCALE + PANEL),
        "paper_height": int(MARGIN * 2 + (max(p[1] for p in allpts) - y0) * SCALE + PANEL),
        "page_count": 1, "page_col_count": 1, "paper_spacing": 50,
        "page_color": "FFFFFF", "orientation": "vertical",
        "legend": "", "legend_collapsed": True, "panels": panels,
    }
    print(json.dumps(fig, indent=2, ensure_ascii=False))
    log(f"Wrote {len(panels)} panels")


if __name__ == "__main__":
    main()
