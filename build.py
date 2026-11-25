#!/usr/bin/env python3
"""Build baekcheolkim.github.io into _site/.

    python3 build.py            build _site/ and update the index in README.md
    python3 build.py --serve    build, then serve _site/ at http://localhost:8000/
    python3 build.py --og-image redraw static/og-image.png, the picture that LinkedIn
                                and other sites show for a shared link (needs Google Chrome)

Needs Python 3.9 or later and markdown-it-py:
    python3 -m pip install -r requirements.txt

The build stops with a list of errors if any page links to a file that does
not exist, so a broken link never reaches the published site.

HOW TO EDIT (README.md has the step-by-step version)
    Your name, headline, links  SITE, just below
    Homepage                    home_page()
    Fig. 1 on the homepage      hbm_figure() here and the HBM part of static/site.js
    Header tabs                 build(), where NAV is filled in
    Header and footer HTML      site_head() and site_foot()
    Standalone pages            PAGES (About, CV, Glossary)
    Link previews, search data  social_tags(), person() and preview_card()
    Colors, fonts, spacing      static/site.css
    Old URLs that must redirect redirects.txt
Content lives in Markdown files; see the table in README.md.
"""

import datetime as dt
import functools
import html
import http.server
import json
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

try:
    from markdown_it import MarkdownIt
except ImportError:
    sys.exit("build.py needs markdown-it-py. Install it with:\n"
             "    python3 -m pip install -r requirements.txt")

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "_site"

# ---------------------------------------------------------------- settings
# Text that appears on the homepage and in every page's header and metadata.
SITE = {
    "name": "Baek C. Kim",                       # header, page titles, feeds
    "url": "https://baekcheolkim.github.io/",       # used for feed and canonical links
    "repo": "https://github.com/BaekCheolKim/BaekCheolKim.github.io",
    "role": "AI Application Analyst · AI/HPC",      # small line above the headline
    "headline": ("I analyze how LLM training and inference map onto GPU supercomputers: "
                 "memory residency, parallel layouts, collective communication."),
    "description": ("TILs, tools and case studies by Baek C. Kim, who analyzes how LLM "
                    "training and inference map onto GPU supercomputers."),
    # "Featured" on the homepage: (link text, link, text after the link)
    "featured": ("AI-Anatomy", "work/ai-anatomy/index.html",
                 "what each GPU holds, where data moves and what each collective costs, "
                 "for five open LLMs on NVIDIA GH200 nodes"),
    "education": "Master of Machine Learning and Computer Vision, Australian National University, 2023–2025",
    # "Elsewhere" on the homepage. A link that starts with http opens another site;
    # other links are pages of this site.
    "links": [("GitHub", "https://github.com/BaekCheolKim"),
              ("LinkedIn", "https://www.linkedin.com/in/baekcheolkim/"),
              ("CV", "cv.html")],
    # Not shown on the pages. Search engines read the first two (see person()),
    # and LinkedIn, Slack and similar sites show preview_image for a shared link.
    "full_name": "Baek Cheol Kim",           # listed as another name, so searches for it find the site
    "job_title": "AI Application Analyst",
    "preview_image": "static/og-image.png",  # 1200 × 630; redraw with python3 build.py --og-image
    # The code from Google Search Console's "HTML tag" check, the part inside
    # content="...". Leave it empty until you set up Search Console (README.md).
    "google_site_verification": "",
}

# Standalone Markdown pages at the top of the repository: (tab name, file, page).
# A page is built and gets a header tab only if its file exists, so creating
# glossary.md is all it takes to add the Glossary.
PAGES = [("Glossary", "glossary.md", "glossary.html"),
         ("CV", "cv.md", "cv.html"),
         ("About", "about.md", "about.html")]

# Kinds of entries in the "Latest" list: label, tab name, singular and plural nouns.
KIND_LABEL = {"til": "TIL", "article": "Article", "tool": "Tool", "work": "Work"}
KIND_TAB = {"til": "TIL", "article": "Articles", "tool": "Tools", "work": "Work"}
KIND_NOUN = {"til": ("TIL", "TILs"), "article": ("article", "articles"),
             "tool": ("tool", "tools"), "work": ("case study", "case studies")}
STREAM_KINDS = ("til", "article", "tool", "work")
STREAM_LIMIT = 80   # the homepage lists at most this many entries

# TIL topic folders are lower-case slugs; these words keep their usual spelling.
TOPIC_WORDS = {"ai": "AI", "api": "API", "cpu": "CPU", "cuda": "CUDA", "gpu": "GPU", "hbm": "HBM",
               "hpc": "HPC", "kv": "KV", "llm": "LLM", "ml": "ML", "moe": "MoE", "mpi": "MPI",
               "nccl": "NCCL", "nvlink": "NVLink", "pdf": "PDF", "pytorch": "PyTorch",
               "rdma": "RDMA", "github": "GitHub", "html": "HTML", "css": "CSS", "js": "JS"}

# Fig. 1 on the homepage. static/site.js holds the same numbers for the buttons,
# so change both together.
HBM_MIB = 97871                      # HBM per GH200 GPU: nvidia-smi's memory.total, measured
TOKENS = 8 * 8192                    # 8 sequences of 8,192 tokens
MODELS = [  # key, button label, parameters, layers, KV heads, head dim, TP degree
    ("8b", "8B · TP 1", 8030261248, 32, 8, 128, 1),
    ("70b", "70B · TP 4", 70553706496, 80, 8, 128, 4),
    ("405b", "405B · TP 4", 405853388800, 126, 8, 128, 4),
]
DEFAULT_MODEL = "70b"

MD = MarkdownIt("commonmark", {"html": True, "xhtmlOut": False}).enable(["table", "strikethrough"])
TODAY = dt.date.today().isoformat()
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August",
               "September", "October", "November", "December"]
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
COMMENT = re.compile(r"<!--.*?-->", re.S)
FRONT = re.compile(r"\A---[ \t]*\n(.*?)\n---[ \t]*\n", re.S)
SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
FIGURE = re.compile(r"<p>(<img [^>]*>)</p>")
ATTR = re.compile(r'\s(href|src)="([^"]*)"')


# ---------------------------------------------------------------- git

def git(*args):
    try:
        done = subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True,
                              text=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return ""
    return done.stdout


def git_state():
    sha = git("rev-parse", "--short", "HEAD").strip()
    dirty = set()
    for line in git("status", "--porcelain", "--untracked-files=all").splitlines():
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        dirty.add(path.strip('"'))
    return sha, dirty


SHA, DIRTY = git_state()


def dates_for(path, meta, errors):
    """Created and updated dates: front matter first, then git history, then today."""
    rel_path = rel(path)
    log = git("log", "--follow", "--format=%as", "--", rel_path).split()
    created = meta.get("date") or (log[-1] if log else TODAY)
    updated = meta.get("updated") or (TODAY if rel_path in DIRTY else (log[0] if log else created))
    for value in (created, updated):
        if not DATE.fullmatch(value):
            errors.append("%s: dates must be YYYY-MM-DD, got %r" % (rel_path, value))
            return TODAY, TODAY
    return created, max(created, updated)


# ---------------------------------------------------------------- text helpers

def esc(text):
    return html.escape(text, quote=True)


def plain(fragment):
    text = re.sub(r"<(script|style)\b.*?</\1>", " ", fragment, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def clip(text, limit):
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0].rstrip(",;:.") + "…"


def first_paragraph(body):
    for match in re.finditer(r"<p>(.*?)</p>", body, re.S):
        text = plain(match.group(1))
        if text:
            return clip(text, 220)
    return ""


def slugify(text):
    text = re.sub(r"<[^>]+>|[`*_~\[\]()]", "", text).lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[\s_-]+", "-", text).strip("-")


def topic_name(slug):
    words = [TOPIC_WORDS.get(w, w) for w in slug.split("-")]
    name = " ".join(words)
    return name[:1].upper() + name[1:]


def short_date(iso, year=True):
    """2026-11-25 -> "25 Nov 2026" (or "25 Nov" inside a month group)."""
    y, m, d = iso.split("-")
    text = "%d %s" % (int(d), MONTHS[int(m) - 1])
    return text + " " + y if year else text


def rel(path):
    return path.relative_to(ROOT).as_posix()


def is_local(url):
    return bool(url) and not SCHEME.match(url) and not url.startswith(("#", "/"))


def plural(n, kind):
    one, many = KIND_NOUN[kind]
    return "%d %s" % (n, one if n == 1 else many)


def newest_first(entries):
    return sorted(entries, key=lambda e: (e.created, e.title.lower()), reverse=True)


# ---------------------------------------------------------------- Markdown

def read_source(path):
    """Front matter (simple "key: value" lines), title and Markdown body.

    Lines in the front matter that start with # are comments.
    """
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    meta = {}
    match = FRONT.match(text)
    if match:
        for line in match.group(1).splitlines():
            key, sep, value = line.partition(":")
            if not sep or not key.strip() or key.lstrip().startswith("#"):
                continue
            value = value.strip()
            if len(value) > 1 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            meta[key.strip().lower()] = value
        text = text[match.end():]
    title = meta.get("title", "")
    lines = text.lstrip("\n").split("\n")
    if lines and lines[0].startswith("# "):
        title = title or lines[0][2:].strip()
        text = "\n".join(lines[1:])
    return meta, title, text


def check_target(url, src, errors):
    target = src.parent / unquote(urlsplit(url).path)
    if not target.exists():
        errors.append("%s: no file at %s" % (rel(src), url))
        return False
    return True


def local_link(url, src, errors):
    """Check a relative link and point links to .md sources at the built .html page."""
    if not is_local(url) or not urlsplit(url).path:
        return url
    if urlsplit(url).path.endswith((".html", "/")):
        return url   # a generated page; check_links() checks it after the build
    if not check_target(url, src, errors):
        return url
    parts = urlsplit(url)
    if parts.path.endswith(".md"):
        return parts.path[:-3] + ".html" + ("#" + parts.fragment if parts.fragment else "")
    return url


def as_figure(match):
    img = match.group(1)
    title = re.search(r' title="([^"]*)"', img)
    if not title:
        return "<figure>%s</figure>" % img
    return "<figure>%s<figcaption>%s</figcaption></figure>" % (img.replace(title.group(0), ""),
                                                               title.group(1))


def render(text, src, errors):
    """Markdown to HTML. Headings get ids and start at h2; relative paths are checked."""
    tokens = MD.parse(COMMENT.sub("", text))
    levels = [int(t.tag[1]) for t in tokens if t.type == "heading_open"]
    shift = max(0, 2 - min(levels)) if levels else 0
    seen = {}
    for i, tok in enumerate(tokens):
        if tok.type in ("heading_open", "heading_close"):
            tok.tag = "h%d" % min(6, int(tok.tag[1]) + shift)
            if tok.type == "heading_open":
                slug = slugify(tokens[i + 1].content) or "section"
                count = seen.get(slug, 0)
                seen[slug] = count + 1
                tok.attrSet("id", slug if count == 0 else "%s-%d" % (slug, count))
        elif tok.type == "inline":
            for child in tok.children or []:
                if child.type == "link_open":
                    child.attrSet("href", local_link(child.attrGet("href") or "", src, errors))
                elif child.type == "image":
                    url = child.attrGet("src") or ""
                    if is_local(url):
                        check_target(url, src, errors)
                    child.attrSet("loading", "lazy")
    out = MD.renderer.render(tokens, MD.options, {})
    return FIGURE.sub(as_figure, out)


def render_inline(text, src, errors):
    tokens = MD.parseInline(text)
    for tok in tokens:
        for child in tok.children or []:
            if child.type == "link_open":
                child.attrSet("href", local_link(child.attrGet("href") or "", src, errors))
    return MD.renderer.render(tokens, MD.options, {})


# ---------------------------------------------------------------- content

class Entry:
    def __init__(self, kind, src, url, title, body, meta, created, updated, topic=None, summary=""):
        self.kind = kind
        self.src = src
        self.url = url              # relative to the site root
        self.title = title
        self.body = body
        self.meta = meta
        self.created = created
        self.updated = updated
        self.topic = topic
        self.summary = summary or meta.get("summary", "") or first_paragraph(body)
        self.text = plain(body)
        self.label = ""             # header tab name, for standalone pages

    @property
    def source(self):
        return rel(self.src)


def load_markdown(kind, pattern, url_for, errors, topic_of=None):
    entries = []
    for path in sorted(ROOT.glob(pattern)):
        if path.name.lower() == "readme.md":
            continue
        meta, title, text = read_source(path)
        if not title:
            errors.append("%s: no title; start the file with '# Title'" % rel(path))
            continue
        created, updated = dates_for(path, meta, errors)
        body = render(text, path, errors)
        entries.append(Entry(kind, path, url_for(path), title, body, meta, created, updated,
                             topic=topic_of(path) if topic_of else None))
    return entries


def load_tools(errors):
    """Tools are single HTML files. Their <title> and description become the listing."""
    entries = []
    for path in sorted((ROOT / "tools").glob("*.html")):
        if path.name == "index.html":
            continue
        text = path.read_text(encoding="utf-8")
        title = re.search(r"<title>(.*?)</title>", text, re.S)
        desc = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', text)
        if not title:
            errors.append("%s: no <title>" % rel(path))
            continue
        name = html.unescape(title.group(1)).split(" · ")[0].strip()
        created, updated = dates_for(path, {}, errors)
        summary = html.unescape(desc.group(1)) if desc else ""
        entries.append(Entry("tool", path, "tools/" + path.name, name, "", {}, created, updated,
                             summary=summary))
    return entries


def load_all(errors):
    content = {
        "til": load_markdown("til", "til/*/*.md",
                             lambda p: "til/%s/%s.html" % (p.parent.name, p.stem), errors,
                             topic_of=lambda p: p.parent.name),
        "article": load_markdown("article", "articles/*.md",
                                 lambda p: "articles/%s.html" % p.stem, errors),
        "work": load_markdown("work", "work/*/index.md",
                              lambda p: "work/%s/index.html" % p.parent.name, errors),
        "tool": load_tools(errors),
        "pages": [],
    }
    for label, filename, url in PAGES:
        path = ROOT / filename
        if path.exists():
            meta, title, text = read_source(path)
            created, updated = dates_for(path, meta, errors)
            entry = Entry("page", path, url, title or label, render(text, path, errors), meta,
                          created, updated)
            entry.label = label
            content["pages"].append(entry)
    return content


# ---------------------------------------------------------------- page frame

NAV = []   # header tabs: (key, label, href, count or None); filled in by build()


def site_head(root, section=""):
    """The header on every page: name, Search and Feed links, then the tabs.

    section is the key of the tab to underline ("home", "til", "tool", "CV", ...).
    """
    tabs = []
    for key, label, href, count in NAV:
        current = ' aria-current="page"' if key == section else ""
        counter = '<span class="Counter">%d</span>' % count if count else ""
        tabs.append('<a href="%s%s"%s>%s%s</a>' % (root, href, current, label, counter))
    return ('<a class="skip" href="#main">Skip to content</a>\n'
            '<header class="site-head">\n'
            '<div class="wrap head-top"><a class="wordmark" href="%sindex.html">%s</a>'
            '<div class="head-aux"><a href="%sindex.html#search">Search</a>'
            '<a href="%sfeed.xml">Feed</a></div></div>\n'
            '<nav class="wrap nav" aria-label="Sections">%s</nav>\n'
            '</header>') % (root, esc(SITE["name"]), root, root, "".join(tabs))


def site_foot(root):
    """The footer on every page: when and from which commit the site was built."""
    if SHA:
        commit = '<a href="%s/commit/%s">%s</a>' % (SITE["repo"], SHA, SHA)
        built = ("a working copy of commit " if DIRTY else "commit ") + commit
    else:
        built = "local files"
    return ('<footer class="site-foot"><div class="wrap">\n'
            '<p>Built by <a href="%s/blob/main/build.py">build.py</a> from %s on %s.</p>\n'
            '<p><a href="%sfeed.xml">Atom feed</a> · <a href="%s">Source on GitHub</a></p>\n'
            '</div></footer>') % (SITE["repo"], built, short_date(TODAY), root, SITE["repo"])


def social_tags(title, description, url, og_type="website"):
    """Open Graph tags: the title, text and picture that LinkedIn, Slack and other
    sites show when someone shares a link to the page. url must be absolute."""
    tags = ['<meta property="og:type" content="%s">' % og_type,
            '<meta property="og:site_name" content="%s">' % esc(SITE["name"]),
            '<meta property="og:title" content="%s">' % esc(title),
            '<meta property="og:description" content="%s">' % esc(description),
            '<meta property="og:url" content="%s">' % esc(url)]
    if (ROOT / SITE["preview_image"]).exists():
        alt = "%s. %s. %s" % (SITE["name"], SITE["role"], SITE["headline"])
        tags += ['<meta property="og:image" content="%s">' % esc(SITE["url"] + SITE["preview_image"]),
                 '<meta property="og:image:width" content="1200">',
                 '<meta property="og:image:height" content="630">',
                 '<meta property="og:image:alt" content="%s">' % esc(alt),
                 '<meta name="twitter:card" content="summary_large_image">']
    return "\n".join(tags)


def person():
    """Who the site is about, in schema.org terms, for search engines. alternateName
    lets a search for the full name find a site that shows the short one."""
    data = {"@type": "Person", "@id": SITE["url"] + "#person", "name": SITE["name"],
            "url": SITE["url"], "jobTitle": SITE["job_title"],
            "sameAs": [url for _, url in SITE["links"] if url.startswith("http")]}
    if SITE["full_name"] and SITE["full_name"] != SITE["name"]:
        data["alternateName"] = SITE["full_name"]
    return data


def json_ld(data):
    """A <script> block of structured data. Search engines read it; browsers ignore it."""
    text = json.dumps(dict({"@context": "https://schema.org"}, **data), ensure_ascii=False)
    return '<script type="application/ld+json">%s</script>' % text.replace("</", "<\\/")


def layout(title, body, root, path, section="", description="", og_type="website",
           scripts=True, head_extra=""):
    """The HTML document around every page except the tools. head_extra is added
    at the end of <head>."""
    full_title = title if title == SITE["name"] else "%s · %s" % (title, SITE["name"])
    canonical = SITE["url"] + path
    description = description or SITE["description"]
    script = '<script src="%sstatic/site.js" defer></script>\n' % root if scripts else ""
    social = social_tags(title, description, canonical, og_type)
    extra = head_extra + "\n" if head_extra else ""
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{canonical}">
<link rel="alternate" type="application/atom+xml" title="{name}" href="{root}feed.xml">
<link rel="icon" href="{root}static/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{root}static/github-markdown.css">
<link rel="stylesheet" href="{root}static/site.css">
{social}
{extra}</head>
<body>
{head}
<main id="main" class="wrap">
{body}
</main>
{foot}
{script}</body>
</html>
""".format(title=esc(full_title), description=esc(description), canonical=esc(canonical),
           name=esc(SITE["name"]), root=root, social=social, extra=extra,
           head=site_head(root, section), body=body, foot=site_foot(root), script=script)


def write(path, text):
    target = OUT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def meta_line(entry):
    """The gray line under a title in a list: the topic for a TIL, else the summary."""
    if entry.kind == "til":
        return topic_name(entry.topic)
    return clip(entry.summary, 150)


def row(entry, root, kind=True, year=True):
    """One entry in a list: date, type label, title and the line under it."""
    label = ('<span class="Label Label--%s">%s</span>' % (entry.kind, KIND_LABEL[entry.kind])
             if kind else "")
    meta = meta_line(entry)
    return ('<li class="row" data-kind="%s"><time datetime="%s">%s</time>%s'
            '<div class="what"><a class="t" href="%s%s">%s</a>%s</div></li>'
            % (entry.kind, entry.created, short_date(entry.created, year), label, root,
               entry.url, esc(entry.title), '<p class="meta">%s</p>' % esc(meta) if meta else ""))


def rows(entries, root, kind=True, year=True):
    cls = "rows" if kind else "rows no-kind"
    items = "\n".join(row(e, root, kind, year) for e in entries)
    return '<ol class="%s">\n%s\n</ol>' % (cls, items)


# ---------------------------------------------------------------- Fig. 1

def hbm_state(key):
    gib = 1024 ** 3
    hbm = HBM_MIB * 1024 ** 2
    _, _, params, layers, kv_heads, head_dim, tp = [m for m in MODELS if m[0] == key][0]
    weights = params * 2 / tp
    kv = 2 * layers * kv_heads * head_dim * 2 * TOKENS / tp
    total = weights + kv
    axis = max(hbm, total) * 1.04
    step = next(s for s in (10, 20, 25, 50, 100, 200, 250, 500, 1000) if axis / gib / s <= 5.5)
    return {"gib": gib, "hbm": hbm, "w": weights, "kv": kv, "total": total, "axis": axis,
            "step": step, "tp": tp}


def hbm_figure(root):
    """Fig. 1 in its default state. site.js redraws it when a model button is pressed."""
    s = hbm_state(DEFAULT_MODEL)
    gib, axis = s["gib"], s["axis"]

    def pct(x):
        return "%.3f%%" % (x / axis * 100)

    over = s["total"] > s["hbm"]
    buttons = "".join(
        '<button type="button" data-model="%s" aria-pressed="%s">%s</button>'
        % (key, "true" if key == DEFAULT_MODEL else "false", label)
        for key, label, *_ in MODELS)
    ticks = []
    value = 0
    while value * gib <= axis * 0.97:
        ticks.append('<span style="left:%s">%d</span>' % (pct(value * gib), value))
        value += s["step"]
    ticks.append('<span class="unit">GiB</span>')
    free = s["hbm"] - s["total"]
    if over:
        status = ("Does not fit: %.1f GiB needed per GPU, %.1f GiB available."
                  % (s["total"] / gib, s["hbm"] / gib))
        if s["w"] > s["hbm"]:
            status += " Weights alone exceed HBM at TP %d." % s["tp"]
    else:
        status = ("Fits: weights and KV cache take %.1f GiB of the %.1f GiB per GPU."
                  % (s["total"] / gib, s["hbm"] / gib))
    return """<figure class="fig Box" id="hbm">
<div class="fig-head Box-header">
<h2 class="fig-title"><span class="fig-no">Fig. 1</span>Per-GPU HBM during inference</h2>
<div class="seg" role="group" aria-label="Model and tensor-parallel degree">{buttons}</div>
</div>
<div class="fig-body">
<div class="plot">
<div class="hbm-track" role="img" id="hbm-track" aria-label="{status}">
<span class="hbm-w" id="hbm-w" style="width:{w}"></span><span class="hbm-kv" id="hbm-kv" style="width:{kv}"></span>
<span class="hbm-over" id="hbm-over" style="left:{cap};width:{ow}"{over_hidden}></span>
<span class="hbm-cap{flip}" id="hbm-cap" style="left:{cap}"><span>HBM {hbm:.1f} GiB</span></span>
</div>
<div class="axis" id="hbm-axis" aria-hidden="true">{ticks}</div>
</div>
<dl class="readout">
<div><dt><i class="key key-w"></i>Weights</dt><dd><span id="hbm-wv">{wv:.1f}</span><small>GiB</small></dd></div>
<div><dt><i class="key key-kv"></i>KV cache</dt><dd><span id="hbm-kvv">{kvv:.1f}</span><small>GiB</small></dd></div>
<div><dt><i class="key {free_key}" id="hbm-fk"></i><span id="hbm-fl">{free_label}</span></dt><dd><span id="hbm-fv">{fv:.1f}</span><small>GiB</small></dd></div>
</dl>
<p class="status{bad}" id="hbm-status">{status}</p>
</div>
<figcaption class="fig-caption">Llama 3.1 with BF16 weights and KV cache for 8 sequences of 8,192 tokens,
split across tensor-parallel (TP) ranks, on one NVIDIA GH200 with 97,871 MiB of HBM
(the total that nvidia-smi reports). Activations, workspace and the CUDA context are not counted.
The formulas come from <a href="{root}work/ai-anatomy/index.html">AI-Anatomy</a>.</figcaption>
</figure>""".format(
        buttons=buttons, w=pct(s["w"]), kv=pct(s["kv"]), cap=pct(s["hbm"]),
        ow=pct(max(0, s["total"] - s["hbm"])), over_hidden="" if over else " hidden",
        flip=" flip" if s["hbm"] / axis > 0.7 else "", hbm=s["hbm"] / gib, ticks="".join(ticks),
        wv=s["w"] / gib, kvv=s["kv"] / gib, fv=abs(free) / gib,
        free_label="Over" if over else "Free", free_key="key-over" if over else "key-free",
        bad=" bad" if over else "", status=esc(status), root=root)


# ---------------------------------------------------------------- pages

def home_page(content, stream):
    """The homepage: introduction, Fig. 1, "Latest" and the side column."""
    tils, works = content["til"], content["work"]
    counts = {k: sum(1 for e in stream if e.kind == k) for k in STREAM_KINDS}
    published = " · ".join(plural(n, k) for k, n in counts.items() if n)
    newest = max([e.updated for e in stream] or [TODAY])
    title, href, text = SITE["featured"]
    facts = [
        ("Featured", '<a href="%s">%s</a>: %s' % (esc(href), esc(title), esc(text))),
        ("Education", esc(SITE["education"])),
        ("Published", esc(published or "Nothing yet")),
        ("Updated", '<time datetime="%s">%s</time>, %s'
         % (newest, short_date(newest), "working copy" if DIRTY else "from git")),
        ("Elsewhere", " · ".join('<a href="%s">%s</a>' % (esc(u), esc(n)) for n, u in SITE["links"])),
    ]
    facts_html = "\n".join("<div><dt>%s</dt><dd>%s</dd></div>" % f for f in facts)

    # Type filters above the list. site.js shows and hides rows when one is pressed.
    tabs = ['<button type="button" data-kind="all" aria-pressed="true">All<span class="Counter">%d</span></button>'
            % len(stream)]
    for k in STREAM_KINDS:
        if counts[k]:
            tabs.append('<button type="button" data-kind="%s" aria-pressed="false">%s<span class="Counter">%d</span></button>'
                        % (k, KIND_TAB[k], counts[k]))

    # Entries grouped by month, newest first.
    groups = []
    for e in stream[:STREAM_LIMIT]:
        key = e.created[:7]
        if not groups or groups[-1][0] != key:
            groups.append((key, []))
        groups[-1][1].append(e)
    months = []
    for key, items in groups:
        year, month = key.split("-")
        months.append('<section class="month"><h3>%s %s</h3>\n%s\n</section>'
                      % (MONTH_NAMES[int(month) - 1], year, rows(items, "", year=False)))
    older = ""
    if len(stream) > STREAM_LIMIT:
        older = '<p class="empty">Older entries are on the TIL, Tools and Work pages.</p>'

    # Side column: TIL topics, case studies, feeds.
    side = []
    if tils:
        topics = {}
        for e in tils:
            topics[e.topic] = topics.get(e.topic, 0) + 1
        items = "".join('<li><a href="til/%s/index.html">%s</a><span class="Counter">%d</span></li>'
                        % (t, esc(topic_name(t)), n)
                        for t, n in sorted(topics.items(), key=lambda x: (-x[1], x[0])))
        side.append('<section><h2>TIL topics</h2><ul>%s</ul></section>' % items)
    if works:
        items = "".join('<li><a href="%s">%s</a></li>' % (e.url, esc(e.title)) for e in newest_first(works))
        side.append('<section><h2>Case studies</h2><ul>%s</ul></section>' % items)
    feeds = '<li><a href="feed.xml">Everything</a><span>Atom</span></li>'
    if tils:
        feeds += '<li><a href="til/feed.xml">TIL only</a><span>Atom</span></li>'
    side.append('<section><h2>Subscribe</h2><ul>%s</ul></section>' % feeds)

    body = """<section class="intro">
<p class="role">{role}</p>
<h1 class="headline">{headline}</h1>
<dl class="facts">
{facts}
</dl>
</section>
{figure}
<div class="home-cols">
<section class="stream" id="stream" aria-labelledby="latest">
<div class="latest-head">
<h2 id="latest">Latest</h2>
<div class="tabs" role="group" aria-label="Show">{tabs}</div>
<div class="search" role="search"><label class="sr-only" for="q">Search entries</label><input id="q" type="search" placeholder="Search" autocomplete="off" spellcheck="false"><kbd>/</kbd></div>
</div>
<div id="stream-list">
{months}
{older}
</div>
<ol class="rows" id="results" hidden></ol>
<p class="empty" id="empty" hidden>No entries match. Try fewer or shorter words.</p>
</section>
<aside class="side" aria-label="More">
{side}
</aside>
</div>""".format(role=esc(SITE["role"]), headline=esc(SITE["headline"]), facts=facts_html,
                 figure=hbm_figure(""), tabs="".join(tabs), months="\n".join(months),
                 older=older, side="\n".join(side))

    # For search engines: the site and the person it is about, and the Search
    # Console code (Google looks for it on the homepage only).
    head = [json_ld({"@graph": [
        {"@type": "WebSite", "@id": SITE["url"] + "#website", "url": SITE["url"],
         "name": SITE["name"], "description": SITE["description"],
         "author": {"@id": SITE["url"] + "#person"}},
        person()]})]
    if SITE["google_site_verification"]:
        head.append('<meta name="google-site-verification" content="%s">'
                    % esc(SITE["google_site_verification"]))
    return layout(SITE["name"], body, "", "", "home", head_extra="\n".join(head))


def entry_meta(entry):
    parts = ['Created <time datetime="%s">%s</time>' % (entry.created, short_date(entry.created))]
    if entry.updated != entry.created:
        parts.append('Updated <time datetime="%s">%s</time>' % (entry.updated, short_date(entry.updated)))
    parts.append('<a href="%s/blob/main/%s">Source</a>' % (SITE["repo"], entry.source))
    parts.append('<a href="%s/commits/main/%s">History</a>' % (SITE["repo"], entry.source))
    return '<p class="entry-meta">%s</p>' % " · ".join(parts)


def til_page(entry, siblings):
    """One TIL: breadcrumbs, title, dates, the Markdown, then other TILs in its topic."""
    root = "../../"
    crumbs = ('<p class="crumbs"><a href="../index.html">TIL</a> / <a href="index.html">%s</a></p>'
              % esc(topic_name(entry.topic)))
    more = ""
    others = [e for e in newest_first(siblings) if e is not entry][:6]
    if others:
        more = ('<nav class="more" aria-label="More in this topic"><h2>More in %s</h2>%s</nav>'
                % (esc(topic_name(entry.topic)), rows(others, root, kind=False)))
    body = ('<article class="entry">\n%s\n<h1 class="entry-title">%s</h1>\n%s\n'
            '<div class="markdown-body">\n%s</div>\n%s\n</article>'
            % (crumbs, esc(entry.title), entry_meta(entry), entry.body, more))
    return layout(entry.title, body, root, entry.url, "til", description=entry.summary,
                  og_type="article")


def article_page(entry):
    root = "../"
    body = ('<article class="entry">\n<p class="crumbs"><a href="index.html">Articles</a></p>\n'
            '<h1 class="entry-title">%s</h1>\n%s\n<div class="markdown-body">\n%s</div>\n</article>'
            % (esc(entry.title), entry_meta(entry), entry.body))
    return layout(entry.title, body, root, entry.url, "article", description=entry.summary,
                  og_type="article")


# Front-matter fields shown in the box at the top of a case study, in this order.
SPEC_FIELDS = [("period", "Period"), ("role", "My role"), ("team", "Team"), ("stack", "Stack")]


def work_page(entry, errors):
    """One case study: title, summary, the facts box, then the Markdown."""
    root = "../../"
    spec = []
    for key, label in SPEC_FIELDS:
        if entry.meta.get(key):
            spec.append("<div><dt>%s</dt><dd>%s</dd></div>"
                        % (label, render_inline(entry.meta[key], entry.src, errors)))
    if entry.meta.get("links"):
        links = []
        for item in entry.meta["links"].split(";"):
            label, _, url = item.partition("|")
            url = url.strip()
            if is_local(url):
                check_target(url, entry.src, errors)
            links.append('<a href="%s">%s</a>' % (esc(url), esc(label.strip())))
        spec.append("<div><dt>Links</dt><dd>%s</dd></div>" % " · ".join(links))
    lede = '<p class="lede">%s</p>' % esc(entry.meta["summary"]) if entry.meta.get("summary") else ""
    body = ('<article class="entry">\n<p class="crumbs"><a href="../index.html">Work</a></p>\n'
            '<h1 class="entry-title">%s</h1>\n%s\n<dl class="spec">%s</dl>\n'
            '<div class="markdown-body">\n%s</div>\n</article>'
            % (esc(entry.title), lede, "".join(spec), entry.body))
    return layout(entry.title, body, root, entry.url, "work", description=entry.summary,
                  og_type="article")


def text_page(entry):
    """About, CV and Glossary: a title and the Markdown. The CV also prints cleanly."""
    note = ""
    if entry.url == "cv.html":
        note = ('<p class="print-note">To save this CV as a PDF, print the page; the header '
                'and footer are left out of the printout.</p>')
    body = ('<article class="entry">\n<h1 class="entry-title">%s</h1>\n%s\n'
            '<div class="markdown-body">\n%s</div>\n</article>' % (esc(entry.title), note, entry.body))
    # About and CV are pages about you, so search engines are told whose they are.
    head = ""
    if entry.url in ("about.html", "cv.html"):
        head = json_ld({"@type": "ProfilePage", "url": SITE["url"] + entry.url,
                        "mainEntity": person()})
    return layout(entry.label, body, "", entry.url, entry.label, description=entry.summary,
                  head_extra=head)


def list_page(title, intro, inner, root, path, section):
    body = '<h1 class="list-title">%s</h1>\n<p class="list-intro">%s</p>\n%s' % (esc(title), intro, inner)
    return layout(title, body, root, path, section)


def til_pages(tils):
    """The TIL index, one page per topic, and one page per TIL."""
    by_topic = {}
    for e in tils:
        by_topic.setdefault(e.topic, []).append(e)
    names = sorted(by_topic, key=lambda t: topic_name(t).lower())
    groups = []
    for t in names:
        items = newest_first(by_topic[t])
        groups.append('<section class="group"><h2><a href="%s/index.html">%s</a><span class="Counter">%d</span></h2>%s</section>'
                      % (t, esc(topic_name(t)), len(items), rows(items, "../", kind=False)))
        write("til/%s/index.html" % t, list_page(
            topic_name(t),
            '%s in this topic. <a href="../index.html">All TILs</a>.' % plural(len(items), "til"),
            '<div class="group">%s</div>' % rows(items, "../../", kind=False),
            "../../", "til/%s/index.html" % t, "til"))
        for e in items:
            write(e.url, til_page(e, items))
    intro = ('Short notes on things I checked, one per page, each with the evidence. %s in %d %s. '
             '<a href="feed.xml">Atom feed</a>.'
             % (plural(len(tils), "til"), len(names), "topic" if len(names) == 1 else "topics"))
    write("til/index.html", list_page("TIL", intro, "\n".join(groups), "../", "til/index.html", "til"))


def simple_list(kind, title, intro, entries):
    folder = {"article": "articles", "tool": "tools", "work": "work"}[kind]
    path = "%s/index.html" % folder
    inner = '<div class="group">%s</div>' % rows(newest_first(entries), "../", kind=False)
    write(path, list_page(title, intro, inner, "../", path, kind))


def tool_page(entry):
    """A tool is copied as it is, with the site header and footer put in place of
    the <!-- site-head --> and <!-- site-foot --> comments. Its canonical link and
    link-preview tags are added before </head>, unless the tool has its own."""
    text = entry.src.read_text(encoding="utf-8")
    if 'property="og:' not in text:
        url = SITE["url"] + entry.url
        tags = '<link rel="canonical" href="%s">\n%s\n' % (
            esc(url), social_tags(entry.title, entry.summary or SITE["description"], url))
        text = text.replace("</head>", tags + "</head>", 1)
    text = text.replace("<!-- site-head -->", site_head("../", "tool"))
    text = text.replace("<!-- site-foot -->", site_foot("../"))
    return text


def page_404():
    body = ('<h1 class="list-title">Page not found</h1>\n'
            '<p class="list-intro">Nothing is published at this address. Pages from the old '
            'site under /docs/ redirect to their new places; this one had no replacement.</p>\n'
            '<p class="list-intro"><a href="/index.html">Go to the homepage</a> or '
            '<a href="/index.html#search">search the site</a>.</p>')
    return layout("Page not found", body, "/", "404.html", scripts=False)


REDIRECT = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Moved</title>
<meta name="robots" content="noindex">
<link rel="canonical" href="{absolute}">
<meta http-equiv="refresh" content="0; url={target}">
</head>
<body>
<p>This page moved to <a href="{target}">{absolute}</a>.</p>
</body>
</html>
"""


def write_redirects(errors):
    """One small page per line of redirects.txt, which sends the browser to the new URL."""
    path = ROOT / "redirects.txt"
    if not path.exists():
        return 0
    count = 0
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) != 2 or not parts[0].startswith("/") or not parts[1].startswith("/"):
            errors.append("redirects.txt:%d: expected '/old/path /new/path'" % number)
            continue
        old, new = parts
        target = unquote(old).lstrip("/")
        if target.endswith("/") or not target:
            target += "index.html"
        if (OUT / target).exists():
            errors.append("redirects.txt:%d: %s is a real page; remove the redirect" % (number, old))
            continue
        write(target, REDIRECT.format(absolute=esc(urljoin(SITE["url"], new)), target=esc(new)))
        count += 1
    return count


# ---------------------------------------------------------------- feeds, search, sitemap

def absolute_urls(fragment, url):
    base = urljoin(SITE["url"], url)

    def fix(match):
        value = match.group(2)
        if SCHEME.match(value) or value.startswith("#"):
            return match.group(0)
        return ' %s="%s"' % (match.group(1), urljoin(base, value))
    return ATTR.sub(fix, fragment)


def atom(entries, path, title):
    entries = newest_first(entries)[:30]
    feed_url = SITE["url"] + path
    updated = max([e.updated for e in entries] or [TODAY])
    items = []
    for e in entries:
        url = SITE["url"] + e.url
        content = absolute_urls(e.body, e.url) if e.body else "<p>%s</p>" % esc(e.summary)
        items.append("""<entry>
<title>{title}</title>
<link href="{url}"/>
<id>{url}</id>
<published>{created}T00:00:00Z</published>
<updated>{updated}T00:00:00Z</updated>
<category term="{kind}"/>
<summary>{summary}</summary>
<content type="html">{content}</content>
</entry>""".format(title=esc(e.title), url=esc(url), created=e.created, updated=e.updated,
                   kind=KIND_LABEL[e.kind], summary=esc(e.summary), content=esc(content)))
    write(path, """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
<title>{title}</title>
<link href="{site}"/>
<link rel="self" href="{feed}"/>
<id>{feed}</id>
<updated>{updated}T00:00:00Z</updated>
<author><name>{name}</name><uri>{site}</uri></author>
{items}
</feed>
""".format(title=esc(title), site=SITE["url"], feed=feed_url, updated=updated,
           name=esc(SITE["name"]), items="\n".join(items)))


def write_search(entries):
    """search.json, which the homepage search box loads on the first keystroke."""
    data = [{"t": e.title, "u": e.url, "k": e.kind, "d": e.created,
             "c": topic_name(e.topic) if e.topic else "", "s": meta_line(e),
             "x": clip(e.summary + " " + e.text, 4000)}
            for e in newest_first(entries)]
    write("search.json", json.dumps(data, ensure_ascii=False, separators=(",", ":")))


def write_sitemap():
    urls = []
    for page in sorted(OUT.rglob("*.html")):
        path = page.relative_to(OUT).as_posix()
        text = page.read_text(encoding="utf-8")
        if path == "404.html" or 'http-equiv="refresh"' in text:
            continue
        urls.append("<url><loc>%s</loc></url>" % esc(SITE["url"] + ("" if path == "index.html" else path)))
    write("sitemap.xml", '<?xml version="1.0" encoding="utf-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s\n</urlset>\n' % "\n".join(urls))


# ---------------------------------------------------------------- README index

def public_url(entry):
    url = SITE["url"] + entry.url
    return url[:-len("index.html")] if url.endswith("/index.html") else url


def update_readme(content):
    """Rewrite the part of README.md between the two index comments."""
    path = ROOT / "README.md"
    start, end = "<!-- index starts -->", "<!-- index ends -->"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    if start not in text or end not in text:
        return
    lines = []
    tils = content["til"]
    if tils:
        lines.append("### TIL\n")
        by_topic = {}
        for e in tils:
            by_topic.setdefault(e.topic, []).append(e)
        for t in sorted(by_topic, key=lambda t: topic_name(t).lower()):
            lines.append("#### %s\n" % topic_name(t))
            for e in newest_first(by_topic[t]):
                lines.append("- [%s](%s) - %s" % (e.title, public_url(e), e.created))
            lines.append("")
    for kind, heading in (("article", "Articles"), ("tool", "Tools"), ("work", "Case studies")):
        if content[kind]:
            lines.append("### %s\n" % heading)
            for e in newest_first(content[kind]):
                lines.append("- [%s](%s) - %s" % (e.title, public_url(e), e.created))
            lines.append("")
    index = "\n".join(lines).strip()
    before, rest = text.split(start, 1)
    after = rest.split(end, 1)[1]
    new = "%s%s\n%s\n%s%s" % (before, start, index, end, after)
    if new != text:
        path.write_text(new, encoding="utf-8")
        print("README.md index updated")


# ---------------------------------------------------------------- link check

def check_links(errors):
    """Every relative or root-relative href/src in the output must resolve to a file."""
    for page in sorted(OUT.rglob("*.html")):
        text = re.sub(r"<script\b.*?</script>", "", page.read_text(encoding="utf-8"), flags=re.S)
        for attr, value in ATTR.findall(text):
            if not value or SCHEME.match(value) or value.startswith(("#", "//")):
                continue
            path = unquote(urlsplit(value).path)
            if not path:
                continue
            target = OUT / path.lstrip("/") if path.startswith("/") else page.parent / path
            if target.is_dir():
                target = target / "index.html"
            if not target.exists():
                errors.append("%s: broken %s %s" % (page.relative_to(OUT).as_posix(), attr, value))


# ---------------------------------------------------------------- link-preview image
# python3 build.py --og-image draws static/og-image.png from preview_card(): the
# site's address, your name, role and headline in GitHub's colors. Redraw it after
# changing those in SITE, then commit the PNG; the build only links to it.

CHROME = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",   # macOS
          "google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]


def preview_card():
    """The 1200 × 630 page that becomes static/og-image.png. Sizes are in pixels."""
    favicon = (ROOT / "static" / "favicon.svg").read_text(encoding="utf-8")
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<style>
html, body {{ margin: 0; width: 1200px; height: 630px; overflow: hidden; }}
body {{
  box-sizing: border-box; padding: 72px 80px; background: #ffffff; color: #1f2328;
  border-bottom: 12px solid #0969da;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif;
}}
.site {{ display: flex; align-items: center; gap: 16px; font-size: 28px; color: #59636e; }}
.site svg {{ width: 44px; height: 44px; }}
h1 {{ margin: 56px 0 0; font-size: 76px; font-weight: 600; line-height: 1.1; }}
.role {{ margin: 16px 0 0; font-size: 32px; color: #59636e; }}
.headline {{ margin: 44px 0 0; font-size: 34px; line-height: 1.4; max-width: 1000px; }}
</style>
</head>
<body>
<div class="site">{favicon}<span>{host}</span></div>
<h1>{name}</h1>
<p class="role">{role}</p>
<p class="headline">{headline}</p>
</body>
</html>
""".format(favicon=favicon, host=esc(urlsplit(SITE["url"]).netloc), name=esc(SITE["name"]),
           role=esc(SITE["role"]), headline=esc(SITE["headline"]))


def find_chrome():
    for name in CHROME:
        path = name if Path(name).is_absolute() else shutil.which(name)
        if path and Path(path).exists():
            return path
    return None


def make_preview_image():
    chrome = find_chrome()
    if not chrome:
        sys.exit("--og-image needs Google Chrome or Chromium, and neither was found.")
    target = ROOT / SITE["preview_image"]
    with tempfile.TemporaryDirectory() as tmp:
        card = Path(tmp) / "card.html"
        card.write_text(preview_card(), encoding="utf-8")
        subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--no-first-run", "--no-default-browser-check",
                        "--user-data-dir=%s" % (Path(tmp) / "profile"),
                        "--force-device-scale-factor=1", "--window-size=1200,630",
                        "--screenshot=%s" % target, card.as_uri()],
                       check=True, capture_output=True, timeout=120)
    width, height = struct.unpack(">II", target.read_bytes()[16:24])   # from the PNG header
    print("Wrote %s: %d × %d pixels, %d KB" % (rel(target), width, height, target.stat().st_size // 1024))
    if (width, height) != (1200, 630):
        print("Expected 1200 × 630. Link previews may crop or scale it.", file=sys.stderr)


# ---------------------------------------------------------------- build

ASSET_DIRS = ("til", "articles", "work")   # their images and PDFs are copied as they are


def build():
    errors = []
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / "static", OUT / "static")
    for folder in ASSET_DIRS:
        for path in (ROOT / folder).rglob("*") if (ROOT / folder).exists() else []:
            if path.is_file() and path.suffix != ".md" and not path.name.startswith("."):
                target = OUT / rel(path)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)

    content = load_all(errors)

    # Header tabs, in this order. A section appears only when it has content;
    # the number after a tab name is how many entries it holds.
    NAV[:] = [("home", "Home", "index.html", None)]
    for key, label, href in (("til", "TIL", "til/index.html"),
                             ("article", "Articles", "articles/index.html"),
                             ("tool", "Tools", "tools/index.html"),
                             ("work", "Work", "work/index.html")):
        if content[key]:
            NAV.append((key, label, href, len(content[key])))
    for page in content["pages"]:
        NAV.append((page.label, page.label, page.url, None))

    stream = newest_first([e for k in STREAM_KINDS for e in content[k]])
    write("index.html", home_page(content, stream))
    if content["til"]:
        til_pages(content["til"])
        atom(content["til"], "til/feed.xml", "%s: TIL" % SITE["name"])
    for e in content["article"]:
        write(e.url, article_page(e))
    for e in content["work"]:
        write(e.url, work_page(e, errors))
    for e in content["tool"]:
        write(e.url, tool_page(e))
    for e in content["pages"]:
        write(e.url, text_page(e))
    if content["article"]:
        simple_list("article", "Articles", "Longer pieces.", content["article"])
    if content["tool"]:
        simple_list("tool", "Tools", "Single-page tools that run in the browser. Each one computes one thing.",
                    content["tool"])
    if content["work"]:
        simple_list("work", "Work", "Case studies: the problem, what I did, the results and their limits.",
                    content["work"])
    write("404.html", page_404())
    redirects = write_redirects(errors)

    atom(stream, "feed.xml", SITE["name"])
    write_search(stream)
    write_sitemap()
    check_links(errors)
    if errors:
        print("Build failed:\n  " + "\n  ".join(errors), file=sys.stderr)
        sys.exit(1)
    update_readme(content)
    print("Built %s: %s; pages: %s; %d redirects."
          % (OUT.relative_to(ROOT), ", ".join(plural(len(content[k]), k) for k in STREAM_KINDS),
             ", ".join(p.label for p in content["pages"]) or "none", redirects))


def serve(port=8000):
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(OUT))
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), handler) as server:
        print("Serving %s at http://localhost:%d/ (Ctrl+C to stop)" % (OUT.relative_to(ROOT), port))
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    if "--og-image" in sys.argv[1:]:
        make_preview_image()
        sys.exit()
    build()
    if "--serve" in sys.argv[1:]:
        serve()
