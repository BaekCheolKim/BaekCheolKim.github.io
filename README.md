# baekcheolkim.github.io

Source of [baekcheolkim.github.io](https://baekcheolkim.github.io/): TILs, tools and case studies by Baek C. Kim on how LLM training and inference run on GPU clusters.

One Python script, `build.py`, turns the Markdown and HTML files in this repository into the website in `_site/`. A push to `main` builds the site again on GitHub and publishes it.

## One-time setup

```sh
python3 -m pip install -r requirements.txt   # installs markdown-it-py, the only dependency
```

## Publish a TIL, step by step

A TIL ("today I learned") is one short Markdown file about one thing you checked.

1. **Pick a topic folder.** TILs live in `til/<topic>/`, for example `til/nccl/` or `til/pytorch/`. Use an existing folder or create a new one. The folder name becomes the topic name on the site: lower case, words joined by hyphens (`kv-cache` becomes "KV cache").

2. **Create the file.** Name it after the content, in lower case with hyphens: `til/nccl/ring-all-reduce-volume.md`. The file name becomes the page address: `/til/nccl/ring-all-reduce-volume.html`.

3. **Write it.** The first line is the title. The first paragraph becomes the summary on lists, in feeds and in search, so make it say the finding.

   ````markdown
   # Ring all-reduce sends 2(n−1)/n of the tensor from each GPU

   With n GPUs, a ring all-reduce is a reduce-scatter followed by an all-gather.
   Each phase sends (n−1)/n of the tensor from every GPU, so the total is 2(n−1)/n.

   ```python
   n = 8
   print(2 * (n - 1) / n)  # 1.75
   ```

   Source: ...
   ````

   Images go in the same folder, linked as `![What the image shows](figure.png)`. A link to another page uses that page's Markdown file, for example `[AI-Anatomy](../../work/ai-anatomy/index.md)`; it works on GitHub and on the site.

4. **Preview it.**

   ```sh
   python3 build.py --serve
   ```

   Open http://localhost:8000/. The TIL is at the top of "Latest" on the homepage, dated today. If the build prints `Build failed`, fix the files it names (usually a link or image path that does not exist) and run the command again. Stop the preview with Ctrl+C.

5. **Commit and push.**

   ```sh
   git add til/nccl/ring-all-reduce-volume.md README.md
   git commit -m "TIL: ring all-reduce volume"
   git push
   ```

   `build.py` also rewrites the index at the bottom of this README, which is why `README.md` is in the commit.

6. **Check the result.** The push starts the "Build and deploy" workflow (the Actions tab on GitHub). It takes about a minute. The TIL then appears on the homepage, on the TIL page, in the topic page and in both Atom feeds. Its date comes from the commit.

To change a TIL later, edit the file and push again; the page shows "Updated" with the date of the latest commit.

## Where to edit what

| To change | Edit |
|---|---|
| Your name, headline, role line, education and "Elsewhere" links on the homepage | `SITE` near the top of `build.py` |
| The order or content of homepage sections | `home_page()` in `build.py` |
| Fig. 1 on the homepage | `MODELS`, `HBM_MIB` and `TOKENS` in `build.py`, and the same constants in `static/site.js` |
| Header tabs | `build()` in `build.py`, where `NAV` is filled in; standalone pages in `PAGES` |
| Colors, fonts, sizes and spacing | `static/site.css`; each section names the part of the page it styles |
| Text of TILs, case studies, About and CV | the Markdown files listed below |
| Old addresses that must keep working | `redirects.txt` |
| The picture shown when a link to the site is shared on LinkedIn, Slack and similar sites | `static/og-image.png`. After changing your name, role or headline in `SITE`, redraw it with `python3 build.py --og-image` (needs Google Chrome) and commit the new PNG |
| What search engines read about you | `full_name`, `job_title` and `google_site_verification` in `SITE`; `person()` in `build.py` |
| The build and deploy steps on GitHub | `.github/workflows/pages.yml` |

### Content files

| Content | Source file | Published at |
|---|---|---|
| TIL | `til/<topic>/<slug>.md` | `/til/<topic>/<slug>.html` |
| Article | `articles/<slug>.md` | `/articles/<slug>.html` |
| Case study | `work/<slug>/index.md`, with its images and PDFs in the same folder | `/work/<slug>/` |
| Tool | `tools/<slug>.html`, one self-contained page | `/tools/<slug>.html` |
| About | `about.md` | `/about.html` |
| CV | `cv.md` | `/cv.html` |
| Glossary (when you add it) | `glossary.md` | `/glossary.html` |

### Rules the build follows

- **Titles:** the first line of a Markdown file is its title (`# Title`). Front matter is optional: lines between two `---` lines at the top, each `key: value`; lines starting with `#` there are comments.
- **Dates:** created is the file's first commit and updated is its latest commit. Uncommitted files show today's date. Front matter `date:` and `updated:` (YYYY-MM-DD) override git.
- **Summaries:** the first paragraph is the summary. Front matter `summary:` overrides it.
- **Case studies:** front matter `period`, `role`, `team`, `stack` and `links` (`Label | URL ; Label | URL`) fill the box at the top of the page. The comments at the top of each `work/*/index.md` repeat this.
- **Tools:** a tool's `<title>` and `<meta name="description">` give its name and summary. The build puts the site header and footer where the tool has `<!-- site-head -->` and `<!-- site-foot -->`, and adds the canonical link and link-preview tags before `</head>` unless the tool has its own `og:` tags.
- **Private notes:** HTML comments (`<!-- … -->`) in Markdown are removed before publishing. Use them for reminders to yourself.
- **Broken links stop the build:** if a page links to a file that does not exist, the build fails and names it.
- **Standalone pages:** `about.md`, `cv.md` and `glossary.md` each get a header tab when the file exists.

The look is GitHub's: `static/github-markdown.css` is GitHub's stylesheet for Markdown ([github-markdown-css](https://github.com/sindresorhus/github-markdown-css), MIT), and `static/site.css` uses GitHub's colors for the rest of the page.

## Search engines and link previews

Every page has Open Graph tags, so a link shared on LinkedIn or Slack shows the page's title, its summary and `static/og-image.png`. The homepage, About and CV also contain schema.org structured data that names you, lists `full_name` as another name, and links your GitHub and LinkedIn profiles.

To have Google index the site and show you which searches find it:

1. Open [Google Search Console](https://search.google.com/search-console) and add a property of the type **URL prefix**: `https://baekcheolkim.github.io/`.
2. Choose the **HTML tag** method. Google shows a tag like `<meta name="google-site-verification" content="abc123…">`. Copy only the `content` value.
3. Paste it into `google_site_verification` in `SITE` in `build.py`, then commit and push.
4. When the deploy has finished, press **Verify** in Search Console.
5. Under **Sitemaps**, submit `sitemap.xml`.

LinkedIn stores a link's preview for some time. After you change the title, summary or picture of a page that was already shared, paste its address into [LinkedIn's Post Inspector](https://www.linkedin.com/post-inspector/) to fetch the preview again.

## Index

`build.py` rewrites this section.

<!-- index starts -->
### TIL

#### Frameworks

- [PyTorch, Megatron Core and NeMo: what each layer of the training stack does](https://baekcheolkim.github.io/til/frameworks/pytorch-megatron-nemo.html) - 2026-11-25

#### GPU

- [What nvidia-smi's 97,871 MiB means on a GH200](https://baekcheolkim.github.io/til/gpu/nvidia-smi-memory-on-gh200.html) - 2026-11-25

#### LLM

- [How large the KV cache is, and how GQA and tensor parallelism divide it](https://baekcheolkim.github.io/til/llm/kv-cache-with-gqa.html) - 2026-11-25
- [Batching alone does not make LLM decode compute-bound on a GH200](https://baekcheolkim.github.io/til/llm/decode-stays-memory-bound.html) - 2026-11-25

#### Networking

- [How GPUs communicate: NVLink, NICs, libfabric and NCCL](https://baekcheolkim.github.io/til/networking/how-gpus-communicate.html) - 2026-11-25

#### Parallelism

- [Mixed-precision Adam keeps 16 bytes per parameter; Megatron's BF16 default keeps 18](https://baekcheolkim.github.io/til/parallelism/zero-bytes-per-parameter.html) - 2026-11-25
- [How the five kinds of parallelism fit together](https://baekcheolkim.github.io/til/parallelism/five-kinds-of-parallelism.html) - 2026-11-25

### Tools

- [Pipeline schedule](https://baekcheolkim.github.io/tools/pipeline-schedule.html) - 2026-11-25

### Case studies

- [AI-Anatomy](https://baekcheolkim.github.io/work/ai-anatomy/) - 2026-10-06
- [Video Call AI](https://baekcheolkim.github.io/work/video-call-ai/) - 2025-01-27
- [Privacy-aware head localization](https://baekcheolkim.github.io/work/privacy-aware-head-localization/) - 2024-11-01
<!-- index ends -->
