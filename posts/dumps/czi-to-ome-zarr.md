(I've still not actually run the pipeline, so I'll likely update this soon.)

**THE TEXT IS AI-GENERATED AND CONTAINS MISTAKES**

# From `.czi` to a public OME-Zarr on the web: the simplest possible path

*Tiago & AI — summary of an AI conversation that may be useful to others.*

*Claude Opus 4.7, 2026-05-13*

---

A walkthrough produced from a conversation about taking one Carl Zeiss CZI file and turning it into a public, browsable OME-Zarr dataset, with as few moving parts as possible. The starting file is the [tulip Airyscan dataset on Zenodo](https://zenodo.org/records/4662053) (record 4662053, CC0, 42 MB). The endpoint is a small HTML page that loads the converted volume from Cloudflare R2 in [Neuroglancer](https://github.com/google/neuroglancer).

The conversation worked through six concrete questions:

1. How do you get **OME-Zarr 0.5** out of `bioformats2raw` (not the default 0.4)?
2. How do you preserve the vendor-specific CZI metadata that doesn't fit cleanly into OME-XML?
3. Where do you put a license file so the data is safe to redistribute?
4. What's the laziest local viewer that handles OME-Zarr 0.5?
5. How do you upload the result to Cloudflare R2 without surprises?
6. How do you embed the result in a static webpage?

The rest of the post follows that order.

---

## 0. Setup

The toolchain is small: Java for `bioformats2raw`, the AWS CLI for talking to R2 (it's S3-compatible), and a Python environment for two or three glue scripts. On a recent Ubuntu:

```bash
sudo apt-get install -y openjdk-21-jre-headless libblosc1 unzip

mkdir -p ~/tools && cd ~/tools
B2R_VERSION=0.11.0   # check https://github.com/glencoesoftware/bioformats2raw/releases
wget -q "https://github.com/glencoesoftware/bioformats2raw/releases/download/v${B2R_VERSION}/bioformats2raw-${B2R_VERSION}.zip"
unzip -q "bioformats2raw-${B2R_VERSION}.zip"
export PATH="$HOME/tools/bioformats2raw-${B2R_VERSION}/bin:$PATH"

python -m venv ~/.venvs/zarr && source ~/.venvs/zarr/bin/activate
pip install "ome-zarr>=0.10" zarr awscli
```

A `conda install -c ome bioformats2raw awscli` works too, if conda is already in the picture. Then fetch the file:

```bash
mkdir -p ~/work/tulip && cd ~/work/tulip
wget -q "https://zenodo.org/records/4662053/files/2021-02-25-tulip_Airyscan.czi"
md5sum 2021-02-25-tulip_Airyscan.czi
# 66602623aa3839ee02427fd0163534c6
```

---

## 1. Convert to OME-Zarr 0.5 in the bioformats2raw layout

This is the step where most outdated tutorials lead people astray. The historical default of `bioformats2raw` was **OME-NGFF 0.4 on Zarr v2**, and that's still what you get if you don't pass any version flag. To get **0.5 on Zarr v3**, the flag is `--ngff-version 0.5`. Some older blog posts call it `--output-version`; that name was never adopted. The current README on the [bioformats2raw repo](https://github.com/glencoesoftware/bioformats2raw) documents `--ngff-version` and says current supported values are `0.4` and `0.5`.

```bash
bioformats2raw \
  --ngff-version 0.5 \
  2021-02-25-tulip_Airyscan.czi \
  tulip.ome.zarr
```

The default output already uses the **bioformats2raw layout**, which means the top-level group is a wrapper, and the actual image lives at `/0`. The structure looks like this:

```
tulip.ome.zarr/
├── zarr.json                # {"ome":{"version":"0.5","bioformats2raw.layout":3}}
├── OME/
│   ├── zarr.json            # {"ome":{"series":["0"]}}
│   └── METADATA.ome.xml     # OME-XML extracted from the CZI
└── 0/
    ├── zarr.json            # multiscales metadata
    ├── 0/                   # full-resolution level
    ├── 1/                   # downsampled
    └── ...
```

A quick parse check:

```bash
python - <<'PY'
import zarr
g = zarr.open("tulip.ome.zarr", mode="r")
print("top:", dict(g.attrs))
print("axes:", g["0"].attrs["ome"]["multiscales"][0]["axes"])
PY
```

This should print axes like `t, c, z, y, x`. The pattern to internalise here is that **every viewer URL ends in `/0`** — pointing at the top group hits the wrapper, not an image, and most tools will either error or render an empty layer. The [OME-Zarr 0.5 spec](https://ngff.openmicroscopy.org/0.5/) has the formal description of the layout.

---

## 2. Export vendor metadata from Fiji

Bio-Formats already extracts the *structured* OME metadata into `OME/METADATA.ome.xml`. CZI files, though, carry a lot of Zeiss-specific information that lives in `OriginalMetadata` annotations: scanner settings, channel emission filters, Airyscan reconstruction parameters, lens names, and so on. Some of it survives the OME-XML conversion as opaque key-value pairs; the human-readable export is easier from [Fiji](https://imagej.net/software/fiji/).

The path in Fiji:

1. `Plugins → Bio-Formats → Bio-Formats Importer`
2. Open the `.czi` file with **Display metadata** and **Display OME-XML metadata** ticked.
3. `Image → Show Info…` to see the full metadata table.
4. `File → Save As… → Text…` to dump it to disk.

The dump goes into a sidecar location inside the dataset:

```bash
mkdir -p tulip.ome.zarr/_extras
mv ~/Downloads/tulip_czi_metadata.txt tulip.ome.zarr/_extras/vendor_metadata.txt
```

The `_extras/` convention is a personal choice, not part of the spec. The OME-Zarr spec doesn't reserve a place for arbitrary vendor blobs, and naming the folder with a leading underscore keeps it out of the way of tools that walk numeric top-level entries assuming each is an image series. The same dump is available headless via the `showinf` tool from [bftools](https://bio-formats.readthedocs.io/en/stable/users/comlinetools/index.html), if scripting later becomes useful.

---

## 3. Add a license file

The Zenodo record marks the file as **CC0**, so redistribution is fine. Baking the license into the dataset means it travels with the bucket:

```bash
cat > tulip.ome.zarr/_extras/LICENSE.txt <<'EOF'
Source: 2021-02-25-tulip_Airyscan.czi
Origin: https://zenodo.org/records/4662053
License: CC0 1.0 Universal (Public Domain Dedication)
        https://creativecommons.org/publicdomain/zero/1.0/

This OME-Zarr representation was produced from the file above using
bioformats2raw (OME-NGFF 0.5, bioformats2raw layout). Also released under CC0.
EOF
```

A README is also worth the thirty seconds:

```bash
cat > tulip.ome.zarr/_extras/README.md <<'EOF'
# Tulip Airyscan — OME-Zarr 0.5

Converted from `2021-02-25-tulip_Airyscan.czi` (Zenodo 4662053, CC0).

- Layout: bioformats2raw layout, image at `/0`
- NGFF version: 0.5 (Zarr v3)
- Vendor metadata: `_extras/vendor_metadata.txt` (from Fiji)
EOF
```

---

## 4. Serve locally and view in Neuroglancer

Neuroglancer is a pure client-side viewer: it fetches Zarr chunks over HTTP and runs everything in WebGL. So the local workflow is just "serve the directory + open the demo URL." [Neuroglancer's README](https://github.com/google/neuroglancer) lists OME-Zarr 0.4 and 0.5 as supported sources.

The browser will refuse cross-origin requests without CORS headers, which `python -m http.server` doesn't send. The smallest fix is a one-file patched server:

```bash
python - <<'PY'
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
class CORS(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()
ThreadingHTTPServer(("127.0.0.1", 8000), CORS).serve_forever()
PY
```

Then open [the Neuroglancer demo](https://neuroglancer-demo.appspot.com/), click **+ Add image layer**, and paste:

```
zarr://http://127.0.0.1:8000/tulip.ome.zarr/0
```

Two things to remember: the **`zarr://`** scheme prefix, and the **`/0`** at the end. [Vizarr](https://github.com/hms-dbmi/vizarr) is a lighter OME-Zarr-only alternative that opens a dataset directly from a URL parameter, no UI clicking needed:

```
https://hms-dbmi.github.io/vizarr/?source=http://127.0.0.1:8000/tulip.ome.zarr/0
```

---

## 5. Upload to Cloudflare R2

R2 speaks the S3 API, so `aws s3` works once you point `--endpoint-url` at the R2 account endpoint. The conversation chose R2 over alternatives like AWS S3 or Backblaze B2 because of **zero egress fees**, which matters once a single OME-Zarr ends up serving thumbnail chunks to the public web.

The five sub-steps:

**Bucket and public access.** In the [Cloudflare R2 dashboard](https://dash.cloudflare.com/), create a bucket (e.g. `ome-zarr-demo`), then under **Settings → Public access → R2.dev subdomain → Allow Access**, which gives a `https://pub-<hash>.r2.dev` URL. For a real deployment, a custom domain replaces this; for a demo the r2.dev subdomain is fine.

**CORS policy.** Under **Settings → CORS Policy → Add CORS policy**:

```json
[
  {
    "AllowedOrigins": ["*"],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedHeaders": ["*"],
    "ExposeHeaders": ["ETag", "Content-Length", "Content-Type"]
  }
]
```

The `["*"]` is fine for a public demo; for a real site it tightens to the website's origin. Full reference at the [R2 CORS docs](https://developers.cloudflare.com/r2/buckets/cors/).

**API token.** Under **R2 → Manage R2 API Tokens**, create one with **Object Read & Write** scoped to the bucket. Save the access key, secret, and account endpoint (`https://<ACCOUNT_ID>.r2.cloudflarestorage.com`).

**AWS CLI config.**

```bash
aws configure --profile r2
# Access Key ID, Secret Access Key from the R2 token
# region: auto, output: json
```

**Sync.** A Zarr directory is a lot of small files; `aws s3 sync` handles it correctly:

```bash
ENDPOINT=https://<ACCOUNT_ID>.r2.cloudflarestorage.com
BUCKET=ome-zarr-demo

aws --profile r2 --endpoint-url "$ENDPOINT" \
  s3 sync tulip.ome.zarr/ "s3://$BUCKET/tulip.ome.zarr/" \
  --checksum-algorithm CRC32
```

A reachability check:

```bash
PUB=https://pub-<your-hash>.r2.dev
curl -sI "$PUB/tulip.ome.zarr/zarr.json"   # expect 200
```

And confirm Neuroglancer still works against the public URL:

```
zarr://https://pub-<your-hash>.r2.dev/tulip.ome.zarr/0
```

**Cache gotcha worth flagging.** If the CORS policy is edited *after* objects are already cached by Cloudflare's CDN, the cached versions will keep being served without CORS headers, and the browser will keep refusing requests. The fix is **Purge Cache** for that hostname after CORS changes. This bites a surprising number of people; it's well-documented in the [community forum](https://community.cloudflare.com/) but easy to miss.

---

## 6. Embed it in a tiny website

Neuroglancer's full state — including the data source URL, axes, and layout — is just a JSON blob URL-encoded after `#!` in the fragment. That means a static `index.html` with a single iframe is enough:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Tulip Airyscan — OME-Zarr demo</title>
  <style>
    html, body { margin: 0; height: 100%; font-family: system-ui, sans-serif; }
    header { padding: 0.75rem 1rem; border-bottom: 1px solid #ddd; }
    header h1 { margin: 0 0 0.25rem 0; font-size: 1.1rem; }
    header p { margin: 0; color: #555; font-size: 0.9rem; }
    iframe { width: 100%; height: calc(100% - 70px); border: 0; }
    a { color: #06c; }
  </style>
</head>
<body>
  <header>
    <h1>Tulip Airyscan — OME-Zarr 0.5 demo</h1>
    <p>
      Source: <a href="https://zenodo.org/records/4662053">Zenodo 4662053</a> (CC0) ·
      Converted with bioformats2raw ·
      Served from Cloudflare R2
    </p>
  </header>
  <iframe id="ng" allow="cross-origin-isolated"></iframe>

  <script>
    const BUCKET = "https://pub-<your-hash>.r2.dev/tulip.ome.zarr";
    const state = {
      dimensions: { x: [1e-6, "m"], y: [1e-6, "m"], z: [1e-6, "m"] },
      layers: [{ type: "image", name: "tulip", source: `zarr://${BUCKET}/0` }],
      layout: "4panel"
    };
    document.getElementById("ng").src =
      "https://neuroglancer-demo.appspot.com/#!" +
      encodeURIComponent(JSON.stringify(state));
  </script>
</body>
</html>
```

Three reasonable ways to host that file:

- **[GitHub Pages](https://pages.github.com/)** — commit the HTML, enable Pages on `main`. Easiest for anything with a Git history.
- **The same R2 bucket** — upload `index.html` next to the data. Works, but R2 doesn't do directory indexing, so the URL is always the full path.
- **[Cloudflare Pages](https://pages.cloudflare.com/)** — separate Pages project pointing at a repo. Cleanest for anything growing beyond one file.

---

## What ends up in the bucket

```
ome-zarr-demo/                       (Cloudflare R2)
├── index.html                       step 6
└── tulip.ome.zarr/
    ├── zarr.json                    step 1: OME-Zarr 0.5 root
    ├── OME/METADATA.ome.xml         step 1: standardised OME metadata
    ├── 0/                           step 1: image + pyramid
    └── _extras/
        ├── vendor_metadata.txt      step 2: full Zeiss key/values
        ├── LICENSE.txt              step 3: CC0 declaration
        └── README.md                step 3: human summary
```

A few things deliberately left out of "simplest possible" but worth coming back to:

- Replace `pub-<hash>.r2.dev` with a **custom domain** for stable URLs.
- Run the [ome-ngff-validator](https://ome.github.io/ome-ngff-validator/) against the dataset to catch metadata mistakes early.
- Use a **Cloudflare Worker** in front of R2 for finer-grained CORS, hotlink protection, or thumbnail generation.
- Swap Neuroglancer for **vizarr** or **[avivator](https://avivator.gehlenborglab.org/)** depending on whether the audience needs 3D, multi-channel composites, or just a quick 2D view.

The full conversion + upload + embed loop, from a fresh shell, takes about ten minutes once the toolchain is installed — most of it spent waiting on the `aws s3 sync` for the chunked output. That's the real point of OME-Zarr on object storage: the slow step is moving bytes, not coercing formats.
