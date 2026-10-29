#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");
const { marked } = require("marked");

const POSTS_DIR = path.join(__dirname, "posts");
const OUT_DIR = path.join(__dirname, "_site");
const SITE_URL = "https://tiago.bio.br/tiago-ai/";
const SITE_TITLE = "tiago-ai";
const SITE_DESC =
  "A blog/dump of AI conversations in the life of a dev/RSE interested in bioimaging, wiki, linked data, iNaturalist and plants.";

const CSS = `
  :root { color-scheme: light dark; --fg: #222; --bg: #fff; --muted: #666; --link: #0066cc; --code: #f4f4f4; --rule: #ddd; }
  @media (prefers-color-scheme: dark) { :root { --fg: #ddd; --bg: #161616; --muted: #999; --link: #6ab0ff; --code: #262626; --rule: #333; } }
  body { font-family: Georgia, serif; max-width: 720px; margin: 40px auto; padding: 0 20px; color: var(--fg); background: var(--bg); line-height: 1.7; }
  a { color: var(--link); text-decoration: none; }
  a:hover { text-decoration: underline; }
  h1 { border-bottom: 1px solid var(--rule); padding-bottom: 8px; }
  img { max-width: 100%; height: auto; }
  pre { background: var(--code); padding: 12px; overflow-x: auto; border-radius: 4px; }
  code { background: var(--code); padding: 2px 4px; border-radius: 3px; font-size: 0.9em; }
  pre code { background: none; padding: 0; }
  table { border-collapse: collapse; display: block; overflow-x: auto; }
  th, td { border: 1px solid var(--rule); padding: 4px 8px; }
  blockquote { border-left: 4px solid var(--rule); margin: 0; padding-left: 16px; color: var(--muted); }
  .back { margin-bottom: 24px; display: inline-block; }
  .date { color: var(--muted); font-size: 0.9em; }
`;

const esc = (s) =>
  s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

function html(title, body, root) {
  return `<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(title)}</title>
<link rel="alternate" type="application/rss+xml" title="${SITE_TITLE}" href="${root}feed.xml">
<style>${CSS}</style></head>
<body>${body}</body>
</html>`;
}

// Date = first git commit of the file (stable across clones), else mtime.
// ponytail: one git call per post, batch via `git log --name-only` if posts reach the hundreds.
function postDate(file) {
  try {
    const out = execFileSync("git", ["log", "--follow", "--diff-filter=A", "--format=%as", "--", file], {
      cwd: POSTS_DIR,
      stdio: ["ignore", "pipe", "ignore"],
    }).toString().trim().split("\n").pop();
    if (out) return out;
  } catch {}
  return fs.statSync(path.join(POSTS_DIR, file)).mtime.toISOString().slice(0, 10);
}

function loadPost(file) {
  const slug = file.replace(/\.md$/, "");
  const md = fs.readFileSync(path.join(POSTS_DIR, file), "utf8");
  const h1 = md.match(/^#\s+(.+)$/m);
  const title = h1
    ? h1[1].replace(/[`*_]/g, "").trim()
    : slug.replace(/[-_]/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  return { slug, title, date: postDate(file), md };
}

function build() {
  fs.rmSync(OUT_DIR, { recursive: true, force: true });
  fs.mkdirSync(OUT_DIR, { recursive: true });

  let files = [];
  try {
    files = fs.readdirSync(POSTS_DIR).filter((f) => f.endsWith(".md"));
  } catch {}
  const posts = files.map(loadPost).sort((a, b) => b.date.localeCompare(a.date) || a.slug.localeCompare(b.slug));

  for (const p of posts) {
    const dir = path.join(OUT_DIR, "post", p.slug);
    fs.mkdirSync(dir, { recursive: true });
    const body = `<a class="back" href="../../">← Back</a>\n<p class="date">${p.date}</p>\n${marked(p.md)}`;
    fs.writeFileSync(path.join(dir, "index.html"), html(p.title, body, "../../"));
  }

  // Non-markdown files in posts/ (images etc.) are copied so posts can reference them.
  for (const f of fs.existsSync(POSTS_DIR) ? fs.readdirSync(POSTS_DIR) : []) {
    if (!f.endsWith(".md")) fs.cpSync(path.join(POSTS_DIR, f), path.join(OUT_DIR, "post", f), { recursive: true });
  }

  const items = posts.length
    ? posts.map((p) => `<li><span class="date">${p.date}</span> — <a href="post/${p.slug}/">${esc(p.title)}</a></li>`).join("\n")
    : "<li>No posts yet — drop a <code>.md</code> file in <code>posts/</code>.</li>";
  const index = `<h1>${SITE_TITLE}</h1>\n<p>${SITE_DESC}</p>\n<ul>${items}</ul>\n<p><a href="feed.xml">RSS</a></p>`;
  fs.writeFileSync(path.join(OUT_DIR, "index.html"), html(SITE_TITLE, index, ""));

  const rssItems = posts
    .map((p) => {
      const url = `${SITE_URL}post/${p.slug}/`;
      return `<item><title>${esc(p.title)}</title><link>${url}</link><guid>${url}</guid><pubDate>${new Date(p.date).toUTCString()}</pubDate></item>`;
    })
    .join("\n");
  fs.writeFileSync(
    path.join(OUT_DIR, "feed.xml"),
    `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>${SITE_TITLE}</title><link>${SITE_URL}</link><description>${esc(SITE_DESC)}</description>
${rssItems}
</channel></rss>\n`
  );
  fs.writeFileSync(path.join(OUT_DIR, "404.html"), html("Not found", `<a class="back" href="${SITE_URL}">← Home</a><p>Not found.</p>`, SITE_URL));

  console.log(`Built ${posts.length} post(s) → _site/`);
}

module.exports = { build, OUT_DIR };
if (require.main === module) build();
