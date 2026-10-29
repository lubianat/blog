# Making GNOME Files show thumbnails for `.ozx` (zipped OME-Zarr)

*From my "Tiago & AI" series — useful bits from my conversations with AI, lightly edited for a general audience.*

---
This post is the result of a long debugging session with Claude Opus 4.7 to get Ubuntu's file manager (Nautilus) to render actual thumbnails for `.ozx` files. Lightly edited.

The short version: Ubuntu already has all the plumbing. You just need to teach it three things — what a `.ozx` file *is*, how to extract a thumbnail from it, and where to find the extractor.

## The idea

A `.ozx` is just a zip file with Zarr inside. If we put a rendered image at a known path inside that zip — say, `Thumbnails/thumbnail.jpg` — then any tool that can unzip can pull it out and show it as a preview.

This is exactly what OpenDocument (`.odt`, `.ods`, `.odp`) has done for twenty years. Every ODF file contains a `Thumbnails/thumbnail.png` at the zip root, and that's why LibreOffice documents show previews in every file manager on Earth. We're borrowing that trick.

This post assumes your `.ozx` already contains a `Thumbnails/thumbnail.jpg` at the zip root. Generating that file from a Zarr pyramid is a separate topic — for now, pretend it's there.

## Prerequisites

A fresh Ubuntu (24.04 or newer) and a `.ozx` file. Check the thumbnail path is where we expect:

```bash
unzip -l your.ozx | grep -i "Thumbnails/thumbnail"
```

You should see something like:

```
    40253  2026-04-15 16:27   Thumbnails/thumbnail.jpg
```

Capital T, lowercase rest, at the zip root (no parent directory in front). If you see `somedir/Thumbnails/thumbnail.jpg` instead, your zip is nested one level too deep — re-zip from *inside* the Zarr directory:

```bash
cd your.ome.zarr/
zip -r -0 ../your.ozx .   # -0 = no compression (Zarr chunks are already compressed)
cd ..
```

## Step 1 — Tell Ubuntu what a `.ozx` is

Every file on Linux has a MIME type. By default `.ozx` gets detected as `application/zip` because that's what its magic bytes say. We need to declare it as its own specific type.

Create the MIME definition:

```bash
sudo tee /usr/share/mime/packages/ozx.xml > /dev/null << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
  <mime-type type="application/vnd.ome.zarr+zip">
    <comment>Zipped OME-Zarr</comment>
    <sub-class-of type="application/zip"/>
    <glob pattern="*.ozx" weight="80"/>
  </mime-type>
</mime-info>
EOF
```

Rebuild the MIME cache so the system picks up the new definition:

```bash
sudo update-mime-database /usr/share/mime
```

Verify:

```bash
gio info your.ozx | grep content-type
```

You should see `application/vnd.ome.zarr+zip`. Ubuntu now knows what `.ozx` is.

## Step 2 — Write the thumbnailer

A thumbnailer is any executable that takes three arguments — input file, output path, requested size — and writes an image to the output path. Ours is one line: extract `Thumbnails/thumbnail.jpg` from the zip.

```bash
sudo tee /usr/local/bin/ozx-thumbnail > /dev/null << 'EOF'
#!/usr/bin/env bash
/usr/bin/unzip -p "$1" "Thumbnails/thumbnail.jpg" > "$2"
EOF
sudo chmod +x /usr/local/bin/ozx-thumbnail
```

Two things worth noticing here.

**Why `/usr/local/bin` and not `~/.local/bin`?** Nautilus runs thumbnailers inside a bubblewrap sandbox — a minimal filesystem namespace that only exposes system paths like `/usr`, `/bin`, `/etc`, and the specific input/output temp files. Your home directory doesn't exist from inside the sandbox. A script at `~/.local/bin/ozx-thumbnail` will fail with a confusing `ENOENT` error, even though it runs perfectly from your shell. This one burned me for a while.

**Why the absolute path `/usr/bin/unzip`?** Same reason — the sandbox has a minimal `PATH`, and a bare `unzip` might not resolve.

Test the script standalone before moving on:

```bash
/usr/local/bin/ozx-thumbnail your.ozx /tmp/probe.jpg 256
file /tmp/probe.jpg
```

You want to see `JPEG image data, ...`.

## Step 3 — Register the thumbnailer

Nautilus looks for thumbnailer definitions in `/usr/share/thumbnailers/`. Each `.thumbnailer` file is a tiny config mapping a MIME type to an executable.

```bash
sudo tee /usr/share/thumbnailers/ozx.thumbnailer > /dev/null << 'EOF'
[Thumbnailer Entry]
TryExec=/usr/local/bin/ozx-thumbnail
Exec=/usr/local/bin/ozx-thumbnail %i %o %s
MimeType=application/vnd.ome.zarr+zip;
EOF
```

The format is simple: `TryExec` is the binary Nautilus checks exists, `Exec` is what actually runs (`%i` = input, `%o` = output, `%s` = size), `MimeType` is the trigger. The trailing semicolon matters — it's a list format.

## Step 4 — Restart and look

Nautilus reads the thumbnailer list on startup and aggressively caches results (including failures). So after any change:

```bash
nautilus -q                    # quit Nautilus
rm -rf ~/.cache/thumbnails/*   # clear success + failure caches
touch your.ozx                 # bump mtime so cache key changes
nautilus ~/path/to/data &      # open Files fresh
```

Wait about 5 seconds. The icon starts as the generic document placeholder, then the thumbnail replaces it.

## Debugging, if it doesn't work

Every time this broke for me, `strace` was the tool that actually told me what was going on. It logs every subprocess Nautilus spawns, so you can see whether your thumbnailer ran, and if it did, what exit code it returned.

```bash
nautilus -q
rm -rf ~/.cache/thumbnails/*
touch your.ozx
strace -f -e trace=execve -o /tmp/nt.trace nautilus ~/path/to/data 2>/dev/null &
sleep 8
pkill -f "strace.*nautilus"
grep -E "ozx-thumb|thumbnail" /tmp/nt.trace
```

Three possible outcomes:

**No matches.** Nautilus doesn't know about your thumbnailer. Check that `/usr/share/thumbnailers/ozx.thumbnailer` exists and that its `MimeType=` matches exactly what `gio info` reports.

**`execve(...) = -1 ENOENT`.** The script path isn't accessible from the sandbox. It must live under `/usr/` — not `~/`, not `/opt/`.

**`execve(...) = 0` but still no thumbnail.** The script ran and exited cleanly, but produced bad output. Run it standalone against the real file and check the result with `file`.

## Caveats

**You need a distinct extension.** Using `.ozx` works because Nautilus dispatches on the final extension. `.ome.zarr.zip` won't work — Nautilus (and Windows Explorer) only read the last segment, so it gets treated as generic zip. This is one of the arguments for adopting `.ozx` as the canonical single-file form for OME-Zarr distribution.

**Folder previews are not really a thing on GNOME.** Nautilus does not dispatch thumbnailers for open directories (`inode/directory`), so an unzipped `.ome.zarr/` folder can't be thumbnailed this way. KDE Dolphin is a partial exception. In practice, `.ozx` is the desktop-friendly form — similar to how ODF documents are always zipped.

**50 MB limit by default.** Nautilus skips thumbnailing for files over 50 MB. You can raise this:

```bash
gsettings set org.gnome.nautilus.preferences thumbnail-limit 500
```

For `.ozx`, reading a thumbnail is a single `unzip -p` regardless of file size, so raising the limit is reasonable.

## What's next

This is a minimum-viable prototype. Real extensions:

- **Fallback paths.** Check multiple conventional paths (ODF-style `Thumbnails/thumbnail.png`, the [size-suffixed `thumbnails/thumbnail_256.jpg` proposed in the OME-Zarr spec discussion](https://github.com/German-BioImaging/ome-zarr-ideas/issues/43)) and use whichever exists. Ideally actually get information from `zarr.json`. 
- **macOS and Windows.** Same zip, same known path, totally different machinery — Quick Look extensions on macOS, MSIX-packaged `IThumbnailProvider` on Windows. The .odt convention is OS-agnostic; only the plumbing changes.

## Why this matters

> NOTE This is the take of AI slop, not mine: 

OME-Zarr is a wonderful format — multiscale pyramids, cloud-friendly, HCS-aware. But until the file manager story is solved, researchers downloading data from IDR see only a generic zip icon. Ten minutes of setup and a one-line bash script change that.

The bet is the same one OpenDocument made twenty years ago: put a thumbnail at a predictable path inside the archive, and the world's file managers will render it. ODF put it at `Thumbnails/thumbnail.png`. OME-Zarr is converging on something similar. The plumbing works, it's standards-based, and it scales from one laptop to every desktop on the planet.

---

*Full thanks to Claude Opus 4.7 for the debugging stamina — we spent a solid hour staring at `strace` output before the sandbox path issue clicked. The discussion continues at [German-BioImaging/ome-zarr-ideas#43](https://github.com/German-BioImaging/ome-zarr-ideas/issues/43).*
