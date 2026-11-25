# A PDF in Markdown image syntax renders as a broken image

The research project page on the old version of this site showed a broken image where its report should have been. It used Markdown image syntax for a PDF, with a path relative to the page:

```markdown
![This is our final report](assets\images\portfolio\Privacy-Aware Perception System for Robotics.pdf)
```

The browser requested `/docs/2portfolio/assets/images/portfolio/Privacy-Aware%20Perception%20System%20for%20Robotics.pdf` and got a 404. There were two separate problems.

**The path was relative to the page.** A URL without a leading `/` resolves against the folder of the page that contains it. The page was `/docs/2portfolio/3Privacy-Aware-Perception-System-for-Robotics.html`, so the browser looked in `/docs/2portfolio/assets/`. The file was in `/assets/images/portfolio/`.

**`![…](…)` produces an `<img>` element.** Even with the right path, Chrome and Firefox do not display a PDF inside `<img>`.

The backslashes did not cause the 404. The [URL Standard](https://url.spec.whatwg.org/) treats `\` as `/` in `http` and `https` URLs, so browsers read both forms as the same path. Other tools do not, so `/` is the safe choice.

The fix is an ordinary link, with the PDF stored next to the page that links it:

```markdown
[Report (PDF, 8 pages)](report.pdf)
```

That is how the [case study](../../work/privacy-aware-head-localization/index.md) links its report now. `build.py` also stops the build when a relative link points at a file that does not exist, so this kind of mistake no longer reaches the published site.
