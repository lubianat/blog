#!/usr/bin/env python3
"""Generate an OMERO.figure JSON (v9) drawing the GerBI logo, one image panel per green dot.

Usage:  python3 make_gerbi_figure.py > gerbi_logo_figure.json

Edit DOTS to fix the layout. Coordinates are in pixels of the 213x161 px
reference logo image; SCALE maps them onto the figure page.
"""
import json
import random

ZARR_URL = "https://livingobjects.ebi.ac.uk/idr/zarr/v0.5/idr0062A/6001240_labels.zarr"

# Wanted on-page colour of the dots (GerBI green). Because OMERO.figure's
# "reverseIntensity" also inverts the LUT, we set the channel to the
# complementary colour and the invert flips it back on a white background.
DOT_COLOR = "0B983A"

# Dot centres measured from the full GerBI logo image (x, y in logo px).
DOTS = [
    # tube: two parallel diagonal columns
    (141.2, 26.0), (155.1, 30.9),
    (136.3, 40.1), (150.0, 45.2),
    (131.1, 54.3), (144.9, 59.3),
    (126.1, 68.6), (139.9, 73.5), (153.8, 73.1),
    (121.0, 82.2), (134.8, 87.2), (161.0, 85.9),
    # arm (right side, curving down)
    (160.5, 101.0), (154.2, 115.0), (150.5, 129.6),
    # stage: angled row, separated from the tube by a grey line
    (97.3, 105.3), (111.5, 110.0), (125.5, 114.4), (139.6, 119.1),
    # base
    (115.1, 145.3), (129.2, 145.3), (143.3, 145.3), (157.5, 145.3),
]

# Grey background dots (lattice in logo px, fitted from the image)
INCLUDE_GREY = True
GREY_COLOR = "DADADA"            # sampled from the logo
GREY_ORIGIN = (80.99, 20.42)
GREY_V1 = (13.595, 4.901)
GREY_V2 = (-5.061, 14.077)
GREY_BOUNDS = (56, 14, 199, 156)  # xmin, ymin, xmax, ymax of the logo square
GREY_CLEARANCE = 9               # skip grey dots closer than this to a green dot

# Random Z plane per dot. Fixed seed = same figure every run; set to None for new picks.
RANDOM_SEED = 42
Z_MIN, Z_MAX = 60, 175   # only used if CELL_VIEWS is empty

# Close-ups on single isolated nuclei, hand-picked in OMERO.figure
# (theZ, zoom %, dx, dy). Every dot gets one of these at random, plus a random
# rotation and flip so repeats don't look identical. The cell stays centred
# because rotation/flip happen around the panel centre.
CELL_VIEWS = [
    (50, 309, 42.83, -35.27),
    (43, 435, 18.90, 36.35),
    (37, 184, 0.0, 0.0),
    (216, 341, 32.72, -6.99),
    (70, 678, 85.42, -0.75),
    (55, 137, -14.55, -4.74),
    (170, 317, 91.92, 7.52),
]
RANDOMISE_ORIENTATION = True

SCALE = 4         # logo px -> figure px
PANEL = 44         # panel width/height in figure px (dots ~14 logo px apart)
MARGIN = 40        # page margin around the dots
WINDOW_END = 1500  # Dapi contrast end; lower (e.g. 700) for stronger colour

# Image metadata (from memory of IDR 6001240 -- verify by adding the image in
# OMERO.figure once and exporting its JSON if panels fail to render).
SHAPES = {"0": [2, 236, 275, 271], "1": [2, 236, 137, 135], "2": [2, 236, 68, 67]}
PX_XY, PX_Z = 0.3603, 0.5002


def complement(hex_color):
    return "%06X" % (0xFFFFFF ^ int(hex_color, 16))


def zarr_attrs():
    multiscale = {
        "name": "6001240_labels.zarr",
        "axes": [{"name": "c", "type": "channel"},
                 {"name": "z", "type": "space", "unit": "micrometer"},
                 {"name": "y", "type": "space", "unit": "micrometer"},
                 {"name": "x", "type": "space", "unit": "micrometer"}],
        "datasets": [{"path": p, "coordinateTransformations": [
            {"type": "scale", "scale": [1, PX_Z, PX_XY * 2 ** i, PX_XY * 2 ** i]}]}
            for i, p in enumerate(SHAPES)],
    }
    return {"multiscales": [multiscale],
            "arrays": {p: {"shape": s, "dtype": "uint16"} for p, s in SHAPES.items()},
            "zarr_version": 3, "version": "0.5"}


def pick_view():
    if CELL_VIEWS:
        z, zoom, dx, dy = random.choice(CELL_VIEWS)
    else:
        z, zoom, dx, dy = random.randint(Z_MIN, Z_MAX), 100, 0, 0
    rot = random.randrange(360) if RANDOMISE_ORIENTATION else 0
    flip = random.random() < 0.5 if RANDOMISE_ORIENTATION else False
    return z, zoom, dx, dy, rot, flip


def panel(x, y, zattrs, color):
    z, zoom, dx, dy, rot, flip = pick_view()
    sizeC, sizeZ, sizeY, sizeX = SHAPES["0"]
    return {
        "imageId": ZARR_URL, "name": "6001240_labels.zarr",
        "x": round(x, 1), "y": round(y, 1), "width": PANEL, "height": PANEL,
        "orig_width": sizeX, "orig_height": sizeY,
        "sizeZ": sizeZ, "theZ": z, "sizeT": 1, "theT": 0,
        "rdefs": {"model": "-"}, "pixelsType": "uint16",
        "pixel_size_x": PX_XY, "pixel_size_y": PX_XY, "pixel_size_z": PX_Z,
        "pixel_size_x_unit": "MICROMETER", "pixel_size_x_symbol": "µm",
        "pixel_size_y_unit": "MICROMETER", "pixel_size_y_symbol": "µm",
        "zoom": zoom, "dx": dx, "dy": dy, "rotation": rot,
        "horizontal_flip": flip, "vertical_flip": False,
        "selected": False, "labels": [], "deltaT": [],
        "channels": [
            {"label": "LaminB1", "active": False, "color": "0000FF", "reverseIntensity": True,
             "window": {"min": 0, "max": 65535, "start": 0, "end": WINDOW_END}},
            {"label": "Dapi", "active": True, "color": complement(color), "reverseIntensity": True,
             "window": {"min": 0, "max": 65535, "start": 0, "end": WINDOW_END}},
        ],
        "zarr": zattrs,
    }


def grey_dots():
    """Background grey dots: a rotated square lattice (fitted to the visible
    grey dots, max error 0.3 px) filling the logo's square, skipping any
    lattice point that would collide with a green dot."""
    import math
    ox, oy = GREY_ORIGIN
    (ax, ay), (bx, by) = GREY_V1, GREY_V2
    xmin, ymin, xmax, ymax = GREY_BOUNDS
    pts = []
    for i in range(-15, 16):
        for j in range(-15, 16):
            x, y = ox + i * ax + j * bx, oy + i * ay + j * by
            if not (xmin <= x <= xmax and ymin <= y <= ymax):
                continue
            if any(math.hypot(x - gx, y - gy) < GREY_CLEARANCE for gx, gy in DOTS):
                continue
            pts.append((x, y))
    return pts


def main():
    random.seed(RANDOM_SEED)
    greens = [(x, y) for x, y in DOTS]
    greys = grey_dots() if INCLUDE_GREY else []
    allpts = greens + greys
    xs = [p[0] for p in allpts]
    ys = [p[1] for p in allpts]
    x0, y0 = min(xs), min(ys)
    zattrs = zarr_attrs()
    # greys first so green panels sit on top if anything overlaps
    panels = [panel(MARGIN + (x - x0) * SCALE, MARGIN + (y - y0) * SCALE, zattrs, GREY_COLOR)
              for x, y in greys]
    panels += [panel(MARGIN + (x - x0) * SCALE, MARGIN + (y - y0) * SCALE, zattrs, DOT_COLOR)
               for x, y in greens]
    width = int(MARGIN * 2 + (max(xs) - x0) * SCALE + PANEL)
    height = int(MARGIN * 2 + (max(ys) - y0) * SCALE + PANEL)
    fig = {
        "version": 9, "figureName": "GerBI logo",
        "page_size": "pixels", "paper_width": width, "paper_height": height,
        "page_count": 1, "page_col_count": 1, "paper_spacing": 50,
        "page_color": "FFFFFF", "orientation": "vertical",
        "legend": "", "legend_collapsed": True, "panels": panels,
    }
    print(json.dumps(fig, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
