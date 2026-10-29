# tiago-ai

A super lightweight blog — drop `.md` files in `posts/` and they appear.

## Usage

```bash
npm install
npm start
# → http://localhost:3000
```

To add a post: drop a `.md` file into `posts/`. Title = its first `# heading`; date = the file's first git commit. Images etc. in `posts/` are copied too (reference as `../name.png`). `npm start` rebuilds on save.

`npm run build` writes `_site/` (index, posts, `feed.xml`, `404.html`); GitHub Actions deploys it to Pages on push to `main`.

## Stack

`build.js` (static generator) + [`marked`](https://marked.js.org/). `server.js` is just a local preview of the built output. No framework, no database. 
