# narsimha-jammula-dev.github.io

Personal resume site, served via GitHub Pages at https://narsimha-jammula-dev.github.io/.

[`resume.json`](resume.json) ([JSON Resume](https://jsonresume.org) format) is the
only file to edit. `build.py` writes every other published form from it:

| File | What it is |
|---|---|
| `index.html` | The page, from `template.html`'s design |
| `resume.txt` | Plain text |
| `resume.pdf` | `index.html` printed by headless Chrome |
| `llms.txt` | Summary for LLM crawlers |
| `sitemap.xml` | Its `lastmod` is `meta.lastModified` |

```sh
python3 build.py           # rebuild everything (the PDF needs Google Chrome)
python3 build.py --check   # exit 1 if a committed file is out of date with resume.json
```

Fields starting `x-` in `resume.json` hold page-only text (hero line, stats,
section tags, repo cards); JSON Resume allows extra fields.

All facts are sourced from the author's own resume. No hidden text or
instructions aimed at automated screeners are present anywhere in this repo.
