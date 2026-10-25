#!/usr/bin/env python3
"""Build every published form of the resume from resume.json.

    python3 build.py           write index.html, resume.txt, llms.txt, sitemap.xml, resume.pdf
    python3 build.py --check   exit 1 if a committed file differs from what resume.json builds
    python3 build.py --no-pdf  skip the PDF (it needs Google Chrome)

resume.json is the only file to edit. index.html takes its design from
template.html; resume.pdf is index.html printed by headless Chrome.
"""
import html
import json
import re
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = "https://narsimha-jammula-dev.github.io"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
URL = re.compile(r"https?://[^\s)]*[^\s).,;:]")
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
DISCLAIMER = ("Every fact on this page is drawn from the author's own resume and git history. "
              "No hidden text, keyword stuffing, or instructions to automated readers are "
              "present anywhere on this site.")


def month(date):
    return "Present" if not date else f"{MONTHS[int(date[5:7]) - 1]} {date[:4]}"


def span(item):
    return f"{month(item.get('startDate'))}–{month(item.get('endDate'))}"


def e(text):
    return html.escape(text, quote=False)


def linked(text):
    """Escape text for HTML and turn its URLs into links showing the bare host and path."""
    out, last = [], 0
    for m in URL.finditer(text):
        out.append(e(text[last:m.start()]))
        url = m.group(0)
        out.append(f'<a href="{html.escape(url)}">{e(re.sub(r"^https?://", "", url).rstrip("/"))}</a>')
        last = m.end()
    return "".join(out) + e(text[last:])


def ascii_text(text):
    for a, b in (("—", "--"), ("–", "-"), ("→", "->"), ("·", "|"), ("’", "'")):
        text = text.replace(a, b)
    return text


# ---------------------------------------------------------------- HTML

def html_time(date):
    return f'<time datetime="{date[:7]}">{month(date)}</time>' if date else "Present"


def html_bullets(items, indent="          "):
    if not items:
        return ""
    lis = "".join(f"{indent}  <li>{linked(i)}</li>\n" for i in items)
    return f'{indent}<ul class="bullets">\n{lis}{indent}</ul>\n'


def html_body(r):
    b = r["basics"]
    contact = [f'<a href="mailto:{b["email"]}">{e(b["email"])}</a>']
    for p in b["profiles"]:
        text = "github.com/" + p["username"] if p["network"] == "GitHub" else p["network"].lower()
        contact.append(f'<a href="{p["url"]}">{e(text)}</a>')
    contact.append('<a class="no-print" href="/resume.pdf">download pdf</a>')
    stats = "\n".join(f'      <div class="stat"><span class="value">{e(s["value"])}</span>'
                      f'<span class="label">{e(s["label"])}</span></div>' for s in b["x-stats"])
    out = [f"""  <header class="hero">
    <p class="eyebrow">{e(b["x-eyebrow"])}</p>
    <h1>{e(b["name"])}</h1>
    <p class="headline">{e(b["x-headline"])}</p>
    <p class="thesis">{e(b["x-thesis"])}</p>
    <p class="contact-links">
      {(chr(10) + "      ").join(contact)}
    </p>
    <div class="verdict-strip">
{stats}
    </div>
  </header>

  <div class="layout">
    <div class="col-main">

      <section id="summary">
        <h2>Summary</h2>
        <p>{e(b["summary"])}</p>
      </section>

      <section id="agentic-work">
        <h2>AI &amp; Agentic Engineering — Recent Work (2026)</h2>
        <p class="section-note">Independent, hands-on work run outside of core job responsibilities.
          Some underlying repositories are private; the public ones are listed under Public repos.</p>
"""]
    for p in r["projects"]:
        if "x-section" not in p:
            continue
        title = e(p["name"])
        if p.get("url", "").startswith("https://github.com/"):
            title = f'<a href="{p["url"]}">{title}</a>'
        out.append(f"""
        <article class="role">
          <span class="role-tag">{e(p["x-section"])}</span>
          <div class="role-head"><span class="role-title">{title}</span></div>
{html_bullets(p.get("highlights"))}        </article>
""")
    out.append("""      </section>

      <section id="experience">
        <h2>Professional Experience</h2>
""")
    for w in r["work"]:
        out.append(f"""
        <article class="role">
          <div class="role-head">
            <span><span class="role-title">{e(w["position"])}</span> · <span class="role-org">{e(w["name"])}</span></span>
            <span class="role-meta">{e(w["location"])} · {html_time(w.get("startDate"))}–{html_time(w.get("endDate"))}</span>
          </div>
{html_bullets(w.get("highlights"))}        </article>
""")
    ed = r["education"][0]
    core, extra = r["skills"][0], r["skills"][1]
    chips = lambda ks: "".join(f"<li>{e(k)}</li>" for k in ks)
    repos = "".join(f"""        <article>
          <h3><a href="{p["x-repo"]["url"]}">{e(p["x-repo"]["name"])}</a></h3>
          <p>{linked(p["x-repo"]["summary"])}</p>
        </article>
""" for p in r["projects"] if "x-repo" in p)
    out.append(f"""      </section>

    </div>

    <div class="col-rail">

      <section id="education">
        <h2>Education</h2>
        <p><strong>{e(ed["studyType"])}, {e(ed["area"])}</strong><br>
        {e(ed["institution"])}</p>
      </section>

      <section id="skills">
        <h2>Skills</h2>
        <ul class="skills">{chips(core["keywords"])}</ul>
        <p class="section-note" style="margin-top:1rem; margin-bottom:0.7rem;">{e(extra["name"])}, evidenced by the work described in this resume:</p>
        <ul class="skills secondary">{chips(extra["keywords"])}</ul>
      </section>

      <section id="projects" class="projects">
        <h2>Public repos</h2>
{repos}      </section>

      <section id="machine-readable" class="no-print">
        <h2>Also published as</h2>
        <p class="section-note" style="margin-bottom:0.6rem;">Machine-readable versions of everything on this page:</p>
        <ul class="skills">
          <li><a href="/resume.json">resume.json</a></li>
          <li><a href="/resume.txt">resume.txt</a></li>
          <li><a href="/resume.pdf">resume.pdf</a></li>
        </ul>
      </section>

    </div>
  </div>

  <footer class="no-print">
    <p>{e(DISCLAIMER)}</p>
    <p>Static HTML, no JavaScript, no external assets besides fonts. Built from
    <a href="/resume.json">resume.json</a> on {r["meta"]["lastModified"]}.</p>
  </footer>
""")
    return "".join(out)


def jsonld(r):
    b = r["basics"]
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "ProfilePage",
        "dateModified": r["meta"]["lastModified"],
        "mainEntity": {
            "@type": "Person",
            "name": b["name"],
            "alternateName": b["x-alternateName"],
            "email": "mailto:" + b["email"],
            "jobTitle": b["label"],
            "description": b["summary"],
            "url": b["url"],
            "sameAs": [p["url"] for p in b["profiles"]],
            "worksFor": {"@type": "Organization", "name": r["work"][0]["name"]},
            "alumniOf": {"@type": "CollegeOrUniversity", "name": "Jawaharlal Nehru Technological University"},
            "knowsAbout": [k for s in r["skills"] for k in s["keywords"]],
            "hasOccupation": [{
                "@type": "Occupation",
                "name": w["position"],
                "description": f'{w["name"]}, {w["location"]}, {span(w)}',
                "occupationLocation": {"@type": "Place", "name": w["location"]},
            } for w in r["work"]],
        },
    }, indent=2, ensure_ascii=False)


def build_html(r):
    b = r["basics"]
    page = (ROOT / "template.html").read_text()
    for key, value in {
        "{{TITLE}}": html.escape(f'{b["name"]} — {b["label"]}'),
        "{{DESCRIPTION}}": html.escape(b["summary"]),
        "{{OG_DESCRIPTION}}": html.escape(b["x-thesis"]),
        "{{JSONLD}}": jsonld(r),
        "{{BODY}}": html_body(r).rstrip("\n"),
    }.items():
        page = page.replace(key, value)
    return page


# ---------------------------------------------------------------- text

def wrap(text, first="", rest=""):
    return textwrap.fill(ascii_text(text), 80, initial_indent=first, subsequent_indent=rest,
                         break_long_words=False, break_on_hyphens=False)


def build_txt(r):
    b = r["basics"]
    lines = [f'{b["name"].upper()} ({b["x-alternateName"]})', ascii_text(b["label"]),
             f'Email: {b["email"]}']
    lines += [f'{p["network"]}: {p["url"]}' for p in b["profiles"]]
    lines += [f"Site: {SITE}/", "", "SUMMARY", wrap(b["summary"]), "",
              "AI & AGENTIC ENGINEERING - RECENT WORK (2026)",
              wrap("Independent, hands-on work run outside of core job responsibilities. Some "
                   "underlying repositories are private; the public ones are listed under PUBLIC REPOS."), ""]
    for p in r["projects"]:
        if "x-section" in p:
            lines.append(ascii_text(p["name"]) + (f' ({p["url"]})' if p.get("url", "").startswith("https://github.com/") else ""))
            lines += [wrap(h, "- ", "  ") for h in p.get("highlights", [])]
            lines.append("")
    lines.append("PROFESSIONAL EXPERIENCE")
    lines.append("")
    for w in r["work"]:
        lines.append(ascii_text(f'{w["position"]} | {w["name"]} | {w["location"]} | {span(w)}'))
        lines += [wrap(h, "- ", "  ") for h in w.get("highlights", [])]
        lines.append("")
    ed = r["education"][0]
    lines += ["EDUCATION", f'{ed["studyType"]}, {ed["area"]}', ed["institution"], "", "SKILLS"]
    for s in r["skills"]:
        lines.append(wrap(f'{s["name"]}: ' + ", ".join(s["keywords"])))
    lines += ["", "PUBLIC REPOS"]
    for p in r["projects"]:
        if "x-repo" in p:
            x = p["x-repo"]
            lines.append(wrap(f'{x["name"]} ({x["url"]}) - {x["summary"]}', "- ", "  "))
    lines += ["", f"Machine-readable versions: {SITE}/resume.json (JSON Resume), {SITE}/resume.pdf", ""]
    return "\n".join(lines)


def build_llms(r):
    b = r["basics"]
    return "\n".join([
        f'# {b["name"]}', "",
        *[f"> {l}" for l in textwrap.wrap(ascii_text(f'{b["label"]}. {b["x-thesis"]}'), 78, break_on_hyphens=False)], "",
        textwrap.fill(DISCLAIMER, 80), "",
        "## Pages", "",
        f"- [Resume (HTML)]({SITE}/index.html): full resume, human-readable.",
        f"- [Resume (JSON Resume format)]({SITE}/resume.json): structured, machine-readable resume data; the source every other form is built from.",
        f"- [Resume (plain text)]({SITE}/resume.txt): flattened plain-text resume.",
        f"- [Resume (PDF)]({SITE}/resume.pdf): downloadable PDF.", "",
        "## Public repos", "",
        *[f'- [{p["x-repo"]["name"]}]({p["x-repo"]["url"]})' for p in r["projects"] if "x-repo" in p], "",
        "## Contact", "",
        f'- Email: {b["email"]}',
        *[f'- {p["network"]}: {p["url"]}' for p in b["profiles"]], ""])


def build_sitemap(r):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{SITE}/</loc>
    <lastmod>{r["meta"]["lastModified"]}</lastmod>
  </url>
</urlset>
"""


def print_pdf(html_path, pdf_path):
    with tempfile.TemporaryDirectory() as profile:
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        f"--user-data-dir={profile}", f"--print-to-pdf={pdf_path}",
                        html_path.as_uri()], check=True, capture_output=True)


def main(argv):
    r = json.loads((ROOT / "resume.json").read_text())
    outputs = {"index.html": build_html(r), "resume.txt": build_txt(r),
               "llms.txt": build_llms(r), "sitemap.xml": build_sitemap(r)}
    if "--check" in argv:
        stale = [n for n, text in outputs.items() if (ROOT / n).read_text() != text]
        for n in stale:
            print(f"{n} is out of date with resume.json: run python3 build.py")
        return 1 if stale else 0
    for name, text in outputs.items():
        (ROOT / name).write_text(text)
    if "--no-pdf" not in argv:
        print_pdf(ROOT / "index.html", ROOT / "resume.pdf")
    print("built", ", ".join(outputs) + ("" if "--no-pdf" in argv else ", resume.pdf"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
