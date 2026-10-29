#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");
const { marked } = require("marked");

const POSTS_DIR = path.join(__dirname, "posts");
const OUT_DIR = path.join(__dirname, "_site");
const SITE_URL = "https://tiago.bio.br/tiago-ai/";
const SITE_TITLE = "Tiago Lubiana";
const SITE_DESC = "Writing by a dev/RSE interested in bioimaging, wiki, linked data, iNaturalist and plants — plus useful AI conversations.";
// Each subfolder of posts/ is a section.
// URLs: /<slug>/ for posts, /<section>/ for section lists, /tag/<tag>/ for tags.
const SECTIONS = {
  blog: { name: "Blog", desc: "Posts that may be AI-supported, but are curated and edited by me." },
  handmade: { name: "Handmade", desc: "Fully human-crafted texts, no AI involved." },
  dumps: { name: "AI dumps", desc: "Raw, unedited AI conversations, shared because they cost time and tokens and don't need to be private.", notice: "Raw AI conversation, unedited. Likely contains mistakes." },
};
// Old URL path → new slug. ponytail: hand-kept; add a line when renaming a published post.
const REDIRECTS = {
  "post/book-editing": "book-editing",
  "post/czi_to_zarr_example": "czi-to-ome-zarr",
  "post/figma_frames": "figma-frames",
  "post/germay_rse_reads": "germany-rse-reads",
  "post/ozx_thumbnails_ubuntu": "ozx-thumbnails-ubuntu",
  "post/hello-world": "",
};
const RESERVED = new Set([...Object.keys(SECTIONS), "tag", "post", "feed.xml", "404.html", "index.html"]);

const CSS = `
  :root { color-scheme: light dark; --fg: #222; --bg: #fdfcfa; --muted: #6b6b6b; --link: #0b5cad; --code: #f2f1ee; --rule: #e2e0dc; --handmade: #2f7d4f; --blog: #0b5cad; --dumps: #a0522d; }
  @media (prefers-color-scheme: dark) { :root { --fg: #ddd; --bg: #161616; --muted: #999; --link: #6ab0ff; --code: #242424; --rule: #333; --handmade: #6cc48f; --blog: #6ab0ff; --dumps: #e0a070; } }
  * { box-sizing: border-box; }
  body { font-family: Georgia, serif; max-width: 720px; margin: 0 auto; padding: 0 16px 48px; color: var(--fg); background: var(--bg); line-height: 1.7; overflow-wrap: break-word; }
  a { color: var(--link); text-decoration: none; }
  a:hover { text-decoration: underline; }
  header.site { display: flex; flex-wrap: wrap; align-items: baseline; gap: 4px 20px; padding: 20px 0; border-bottom: 1px solid var(--rule); margin-bottom: 28px; font-family: system-ui, sans-serif; }
  header.site .brand { font-weight: 700; color: var(--fg); margin-right: auto; }
  header.site nav a { margin-left: 14px; color: var(--muted); }
  header.site nav a.on { color: var(--fg); font-weight: 600; }
  h1 { line-height: 1.25; }
  img, iframe, video { max-width: 100%; }
  iframe { width: 100%; min-height: 70vh; border: 1px solid var(--rule); }
  pre { background: var(--code); padding: 12px; overflow-x: auto; border-radius: 4px; }
  code { background: var(--code); padding: 2px 4px; border-radius: 3px; font-size: 0.9em; }
  pre code { background: none; padding: 0; }
  table { border-collapse: collapse; display: block; overflow-x: auto; }
  th, td { border: 1px solid var(--rule); padding: 4px 8px; }
  blockquote { border-left: 4px solid var(--rule); margin: 0; padding-left: 16px; color: var(--muted); }
  .meta, .date { color: var(--muted); font-size: 0.9em; font-family: system-ui, sans-serif; }
  .badge { font: 600 0.72em system-ui, sans-serif; text-transform: uppercase; letter-spacing: .05em; padding: 1px 6px; border-radius: 3px; border: 1px solid currentColor; }
  .badge.handmade { color: var(--handmade); } .badge.blog { color: var(--blog); } .badge.dumps { color: var(--dumps); }
  .tags a { margin-right: 8px; }
  ul.posts { list-style: none; padding: 0; }
  ul.posts li { padding: 10px 0; border-bottom: 1px solid var(--rule); }
  ul.posts .title { display: block; font-size: 1.1em; }
  #q { width: 100%; padding: 8px 10px; font: inherit; border: 1px solid var(--rule); border-radius: 4px; background: var(--bg); color: var(--fg); }
  .notice { border-left: 4px solid var(--dumps); padding: 4px 12px; color: var(--muted); font-size: .9em; }
  footer { margin-top: 48px; color: var(--muted); font: 0.85em system-ui, sans-serif; }
`;

// ponytail: client-side filter over the rendered list, real search index if posts reach the thousands.
const SEARCH_JS = `<script>
const q = document.getElementById("q");
q.addEventListener("input", () => {
  const t = q.value.toLowerCase();
  for (const li of document.querySelectorAll("ul.posts li")) li.hidden = !li.textContent.toLowerCase().includes(t);
});
</script>`;

const esc = (s) =>
  String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const tagSlug = (t) => t.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

function html(title, body, root, active = "") {
  const nav = [["", "All"], ...Object.entries(SECTIONS).map(([k, s]) => [`${k}/`, s.name])]
    .map(([href, name]) => `<a href="${root}${href}"${active === href ? ' class="on"' : ""}>${name}</a>`)
    .join("");
  return `<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(title)}</title>
<link rel="alternate" type="application/rss+xml" title="${SITE_TITLE}" href="${root}feed.xml">
<style>${CSS}</style></head>
<body>
<header class="site"><a class="brand" href="${root}">${SITE_TITLE}</a><nav>${nav}<a href="${root}feed.xml">RSS</a></nav></header>
<main>${body}</main>
<footer>No ads, no algorithms. Source on GitHub.</footer>
</body>
</html>`;
}

// Date = first git commit of the file (stable across clones), else mtime. Front matter `date:` wins.
// ponytail: one git call per post, batch via `git log --name-only` if posts reach the hundreds.
function gitDate(file) {
  try {
    const out = execFileSync("git", ["log", "--follow", "--diff-filter=A", "--format=%as", "--", file], {
      cwd: POSTS_DIR,
      stdio: ["ignore", "pipe", "ignore"],
    }).toString().trim().split("\n").pop();
    if (out) return out;
  } catch {}
  return fs.statSync(path.join(POSTS_DIR, file)).mtime.toISOString().slice(0, 10);
}

// Optional `---\nkey: value\n---` header; only flat string keys.
function frontMatter(src) {
  const m = src.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n/);
  if (!m) return [{}, src];
  const meta = {};
  for (const line of m[1].split(/\r?\n/)) {
    const i = line.indexOf(":");
    if (i > 0) meta[line.slice(0, i).trim()] = line.slice(i + 1).trim();
  }
  return [meta, src.slice(m[0].length)];
}

function loadPost(section, file) {
  const slug = file.replace(/\.md$/, "");
  const [meta, md] = frontMatter(fs.readFileSync(path.join(POSTS_DIR, section, file), "utf8"));
  const h1 = md.match(/^#\s+(.+)$/m);
  const title =
    meta.title ||
    (h1 ? h1[1].replace(/[`*_]/g, "").trim() : slug.replace(/[-_]/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()));
  const tags = (meta.tags || "").split(",").map((t) => t.trim()).filter(Boolean);
  return { slug, section, title, tags, date: meta.date || gitDate(path.join(section, file)), md, hasH1: !!h1 };
}

const tagLinks = (tags, root) =>
  tags.length ? `<span class="tags">${tags.map((t) => `<a href="${root}tag/${tagSlug(t)}/">#${esc(t)}</a>`).join("")}</span>` : "";

function list(posts, root) {
  if (!posts.length) return "<p>Nothing here yet.</p>";
  const items = posts
    .map(
      (p) => `<li><a class="title" href="${root}${p.slug}/">${esc(p.title)}</a>
<span class="meta">${p.date} · <span class="badge ${p.section}">${SECTIONS[p.section].name}</span> ${tagLinks(p.tags, root)}</span></li>`
    )
    .join("\n");
  return `<input id="q" type="search" placeholder="Filter posts…" aria-label="Filter posts"><ul class="posts">${items}</ul>${SEARCH_JS}`;
}

function write(rel, content) {
  const file = path.join(OUT_DIR, rel);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, content);
}

function build() {
  fs.rmSync(OUT_DIR, { recursive: true, force: true });
  fs.mkdirSync(OUT_DIR, { recursive: true });

  const posts = [];
  const seen = new Set();
  for (const section of Object.keys(SECTIONS)) {
    const dir = path.join(POSTS_DIR, section);
    if (!fs.existsSync(dir)) continue;
    for (const f of fs.readdirSync(dir)) {
      if (!f.endsWith(".md")) {
        // Images, PDFs etc. land at the site root; reference as ../name from a post.
        if (f.startsWith(".")) continue;
        if (RESERVED.has(f) || seen.has(f)) throw new Error(`posts/${section}/${f} clashes with a reserved or existing path`);
        seen.add(f);
        fs.cpSync(path.join(dir, f), path.join(OUT_DIR, f), { recursive: true });
        continue;
      }
      const p = loadPost(section, f);
      if (seen.has(p.slug) || RESERVED.has(p.slug)) throw new Error(`Slug "${p.slug}" in posts/${section}/ is taken or reserved`);
      seen.add(p.slug);
      posts.push(p);
    }
  }
  posts.sort((a, b) => b.date.localeCompare(a.date) || a.slug.localeCompare(b.slug));

  for (const p of posts) {
    const root = "../";
    const n = SECTIONS[p.section].notice;
    const notice = n ? `<p class="notice">${n}</p>` : "";
    const head = p.hasH1 ? "" : `<h1>${esc(p.title)}</h1>`;
    const body = `<article>${head}<p class="meta">${p.date} · <span class="badge ${p.section}">${SECTIONS[p.section].name}</span> ${tagLinks(p.tags, root)}</p>${notice}
${marked(p.md)}</article>`;
    write(`${p.slug}/index.html`, html(p.title, body, root, `${p.section}/`));
  }

  write("index.html", html(SITE_TITLE, `<p>${esc(SITE_DESC)}</p>${list(posts, "")}`, "", ""));
  for (const [k, s] of Object.entries(SECTIONS)) {
    const body = `<h1>${s.name}</h1><p>${esc(s.desc)}</p>${list(posts.filter((p) => p.section === k), "../")}`;
    write(`${k}/index.html`, html(`${s.name} — ${SITE_TITLE}`, body, "../", `${k}/`));
  }

  const byTag = {};
  for (const p of posts) for (const t of p.tags) (byTag[tagSlug(t)] ||= { name: t, posts: [] }).posts.push(p);
  for (const [slug, { name, posts: ps }] of Object.entries(byTag)) {
    write(`tag/${slug}/index.html`, html(`#${name} — ${SITE_TITLE}`, `<h1>#${esc(name)}</h1>${list(ps, "../../")}`, "../../"));
  }

  const rssItems = posts
    .map((p) => {
      const url = `${SITE_URL}${p.slug}/`;
      return `<item><title>${esc(p.title)}</title><link>${url}</link><guid>${url}</guid><category>${SECTIONS[p.section].name}</category><pubDate>${new Date(p.date).toUTCString()}</pubDate></item>`;
    })
    .join("\n");
  write(
    "feed.xml",
    `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>${esc(SITE_TITLE)}</title><link>${SITE_URL}</link><description>${esc(SITE_DESC)}</description>
${rssItems}
</channel></rss>\n`
  );
  for (const [from, to] of Object.entries(REDIRECTS)) {
    write(`${from}/index.html`, `<!DOCTYPE html><meta charset="UTF-8"><link rel="canonical" href="${SITE_URL}${to && to + "/"}"><meta http-equiv="refresh" content="0; url=${SITE_URL}${to && to + "/"}">`);
  }
  write("404.html", html("Not found", `<h1>Not found</h1><p><a href="${SITE_URL}">← Home</a></p>`, SITE_URL));

  console.log(`Built ${posts.length} post(s), ${Object.keys(byTag).length} tag(s) → _site/`);
}

module.exports = { build, OUT_DIR };
if (require.main === module) build();
