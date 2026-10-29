# blog

A super lightweight blog — drop `.md` files in `posts/` and they appear.

## Usage

```bash
npm install
npm start
# → http://localhost:3000
```

Posts live in three sections:

- `posts/handmade/` → `/handmade/`: fully human-crafted texts
- `posts/blog/` → `/blog/`: curated posts that may be AI-supported
- `posts/dumps/` → `/dumps/`: raw, unedited AI conversations, kept because they cost time and tokens and don't need to be private

Each post is served at `/<filename>/` whatever its section, so moving a post between sections keeps its URL. Use kebab-case filenames. Optional front matter:

```
---
title: My title
date: 2025-04-23
tags: wikidata, ontology
---
```

By default the title is the first `# heading` and the date is the file's first git commit. Raw HTML is fine. Images and PDFs in a section folder are copied to the site root; reference them as `../name.pdf`. Slugs must be unique and can't be a section name or `tag` (the build fails if they are). If you rename a published post, add its old path to `REDIRECTS` in `build.js`. Tag pages and a filter box are generated. `npm start` rebuilds on save.

`npm run build` writes `_site/` (index, posts, `feed.xml`, `404.html`); GitHub Actions deploys it to Pages on push to `main`.

## Stack

`build.js` (static generator) + [`marked`](https://marked.js.org/). `server.js` is just a local preview of the built output. No framework, no database. 
