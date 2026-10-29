// Dev preview: builds the same _site/ that gets deployed, serves it, and rebuilds when posts/ changes.
const http = require("http");
const fs = require("fs");
const path = require("path");
const { build, OUT_DIR } = require("./build");

const PORT = process.env.PORT || 3000;
const TYPES = { ".html": "text/html; charset=utf-8", ".xml": "application/rss+xml", ".png": "image/png", ".jpg": "image/jpeg", ".svg": "image/svg+xml", ".gif": "image/gif", ".webp": "image/webp" };

build();
let timer;
fs.watch(path.join(__dirname, "posts"), () => {
  clearTimeout(timer);
  timer = setTimeout(build, 100);
});

http
  .createServer((req, res) => {
    const rel = decodeURIComponent(new URL(req.url, "http://x").pathname);
    let file = path.join(OUT_DIR, rel);
    if (!file.startsWith(OUT_DIR)) return res.writeHead(400).end();
    if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, "index.html");
    fs.readFile(file, (err, data) => {
      if (err) {
        res.writeHead(404, { "Content-Type": TYPES[".html"] });
        return res.end(fs.readFileSync(path.join(OUT_DIR, "404.html")));
      }
      res.writeHead(200, { "Content-Type": TYPES[path.extname(file)] || "application/octet-stream" });
      res.end(data);
    });
  })
  .listen(PORT, () => console.log(`Preview at http://localhost:${PORT}`));
