#!/usr/bin/env python3
"""Build the CV: content/cv.<lang>.toml -> dist/cv.<lang>.html -> dist/cv.<lang>.pdf

Stdlib only (Python 3.11+) plus Google Chrome for the PDF step.
"""

from __future__ import annotations

import argparse
import html
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
TEMPLATE = ROOT / "template"
DIST = ROOT / "dist"

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "google-chrome",
    "chromium",
]


# --------------------------------------------------------------------------
# inline markup: **bold** and `mono`
# --------------------------------------------------------------------------

def rich(text: str) -> str:
    """Escape HTML, then re-enable **bold** and `mono`."""
    out = html.escape(str(text), quote=False)
    out = re.sub(r"`([^`]+)`", r'<code>\1</code>', out)
    out = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", out)
    return out


def esc(text: str) -> str:
    return html.escape(str(text), quote=True)


# --------------------------------------------------------------------------
# section renderers
# --------------------------------------------------------------------------

def render_header(cv: dict) -> str:
    p = cv["profile"]
    links = []
    for link in p.get("links", []):
        value = esc(link["value"])
        href = link.get("href")
        links.append(
            f'<a href="{esc(href)}">{value}</a>' if href else f"<span>{value}</span>"
        )
    sep = '<span class="dot" aria-hidden="true">/</span>'
    return f"""
  <header class="masthead">
    <h1>{esc(p['name'])}</h1>
    <p class="headline">{rich(p['headline'])}</p>
    <p class="contact">{sep.join(links)}</p>
  </header>
"""


def render_summary(cv: dict) -> str:
    p = cv["profile"]
    if not p.get("summary"):
        return ""
    labels = cv.get("labels", {})
    return f"""
  <section class="row summary">
    {rail(labels.get('summary', 'Profile'))}
    <div class="body"><p class="lede">{rich(p['summary'].strip())}</p></div>
  </section>
"""


def render_highlights(cv: dict) -> str:
    items = cv.get("highlights", [])
    if not items:
        return ""
    labels = cv.get("labels", {})
    tiles = "".join(
        f'<li><span class="figure">{rich(h["value"])}</span>'
        f'<span class="caption">{rich(h["label"])}</span></li>'
        for h in items
    )
    return f"""
  <section class="row highlights">
    {rail(labels.get('highlights', 'Impact'))}
    <div class="body"><ul class="tiles">{tiles}</ul></div>
  </section>
"""


def group_by_company(entries: list[dict]) -> list[tuple[str, list[dict]]]:
    """Fold consecutive entries sharing a company into one group."""
    groups: list[tuple[str, list[dict]]] = []
    for entry in entries:
        company = entry.get("company", "")
        if groups and groups[-1][0] == company:
            groups[-1][1].append(entry)
        else:
            groups.append((company, [entry]))
    return groups


def render_role(role: dict, *, with_company: bool) -> str:
    dates = f"{role.get('start', '')}"
    if role.get("end"):
        dates = f"{dates} – {role['end']}" if dates else role["end"]

    bits = []
    if with_company:
        if role.get("company"):
            bits.append(f'<span class="org">{esc(role["company"])}</span>')
        if role.get("location"):
            bits.append(f'<span class="where">{esc(role["location"])}</span>')
    meta = '<span class="dot" aria-hidden="true">/</span>'.join(bits)

    context = (
        f'<p class="context">{rich(role["context"])}</p>' if role.get("context") else ""
    )
    bullets = "".join(f"<li>{rich(b)}</li>" for b in role.get("bullets", []))
    bullets = f"<ul class=\"achievements\">{bullets}</ul>" if bullets else ""
    tech = "".join(f"<li>{esc(t)}</li>" for t in role.get("tech", []))
    tech = f'<ul class="tech">{tech}</ul>' if tech else ""

    return f"""
        <article class="role">
          <div class="role-head">
            <h4>{rich(role.get('role', ''))}</h4>
            <p class="when">{esc(dates)}</p>
          </div>
          {f'<p class="role-meta">{meta}</p>' if meta else ''}
          {context}
          {bullets}
          {tech}
        </article>
"""


def render_experience(cv: dict) -> str:
    entries = cv.get("experience", [])
    if not entries:
        return ""
    labels = cv.get("labels", {})
    blocks = []
    for company, roles in group_by_company(entries):
        multi = len(roles) > 1
        header = ""
        if multi:
            # One employer header, then the titles held under it.
            first = roles[0]
            span = f"{roles[-1].get('start', '')} – {first.get('end', '')}"
            where = first.get("location", "")
            header = (
                f'<div class="employer"><h3>{esc(company)}</h3>'
                f'<p class="employer-meta">{esc(where)}'
                f'<span class="dot" aria-hidden="true">/</span>{esc(span)}</p></div>'
            )
        else:
            roles[0].setdefault("company", company)
        body = "".join(render_role(r, with_company=not multi) for r in roles)
        blocks.append(f'<div class="job">{header}{body}</div>')

    return f"""
  <section class="row experience">
    {rail(labels.get('experience', 'Experience'))}
    <div class="body">{''.join(blocks)}</div>
  </section>
"""


def render_skills(cv: dict) -> str:
    groups = cv.get("skills", [])
    if not groups:
        return ""
    labels = cv.get("labels", {})
    rows = "".join(
        f'<div class="skill"><dt>{esc(g["label"])}</dt>'
        f'<dd>{rich(" · ".join(g["items"]))}</dd></div>'
        for g in groups
    )
    return f"""
  <section class="row skills">
    {rail(labels.get('skills', 'Toolkit'))}
    <div class="body"><dl class="skill-grid">{rows}</dl></div>
  </section>
"""


def rail(label: str) -> str:
    """Rail heading. Labels too long for the gutter get a smaller setting."""
    cls = ' class="long"' if len(label) > 10 else ""
    return f'<div class="rail"><h2{cls}>{esc(label)}</h2></div>'


def render_listing(cv: dict, key: str, default_label: str) -> str:
    entries = cv.get(key, [])
    if not entries:
        return ""
    labels = cv.get("labels", {})
    rows = []
    for e in entries:
        right = []
        if e.get("detail"):
            right.append(f'<p class="detail">{rich(e["detail"])}</p>')
        rows.append(
            f"""
        <div class="line">
          <div class="line-main">
            <h4>{rich(e.get('title', ''))}</h4>
            {f'<p class="sub">{rich(e["sub"])}</p>' if e.get('sub') else ''}
            {''.join(right)}
          </div>
          {f'<p class="when">{esc(e["when"])}</p>' if e.get('when') else ''}
        </div>"""
        )
    return f"""
  <section class="row {key}">
    {rail(labels.get(key, default_label))}
    <div class="body">{''.join(rows)}</div>
  </section>
"""


def render_closing(cv: dict) -> str:
    block = cv.get("closing")
    if not block:
        return ""
    labels = cv.get("labels", {})
    rows = "".join(
        f'<div class="skill"><dt>{esc(g["label"])}</dt>'
        f'<dd>{rich(g["value"])}</dd></div>'
        for g in block.get("groups", [])
    )
    return f"""
  <section class="row closing">
    {rail(labels.get('closing', 'Also'))}
    <div class="body"><dl class="skill-grid">{rows}</dl></div>
  </section>
"""


# --------------------------------------------------------------------------
# page assembly
# --------------------------------------------------------------------------

def render(cv: dict, css: str, paper: str) -> str:
    meta = cv.get("meta", {})
    lang = meta.get("lang", "en")
    accent = meta.get("accent", "#0e5a63")
    base_pt = meta.get("base_pt", 10)
    name = cv["profile"]["name"]
    title = f"{name} — {cv['profile']['headline']}"

    sections = [
        render_header(cv),
        render_summary(cv),
        render_highlights(cv),
        render_experience(cv),
        render_skills(cv),
        render_listing(cv, "certifications", "Certifications"),
        render_listing(cv, "earlier", "Earlier"),
        render_listing(cv, "education", "Education"),
        render_closing(cv),
    ]

    page_size = "8.5in 11in" if paper == "letter" else "210mm 297mm"

    return f"""<!doctype html>
<html lang="{esc(lang)}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<style>
@page {{ size: {page_size}; margin: 14mm 15mm; }}
{css}
/* Per-document overrides last, so they win over the stylesheet's defaults. */
:root {{ --accent: {accent}; --base: {base_pt}pt; }}
</style>
</head>
<body>
<main class="sheet">
{''.join(sections)}
</main>
</body>
</html>
"""


# --------------------------------------------------------------------------
# pdf
# --------------------------------------------------------------------------

def find_chrome() -> str | None:
    for candidate in CHROME_CANDIDATES:
        if Path(candidate).exists():
            return candidate
        found = shutil.which(candidate)
        if found:
            return found
    return None


def page_count(pdf_path: Path) -> int:
    """Cheap page count straight out of the PDF object tree."""
    return len(re.findall(rb"/Type\s*/Page[^s]", pdf_path.read_bytes()))


def to_pdf(html_path: Path, pdf_path: Path) -> bool:
    chrome = find_chrome()
    if not chrome:
        print("  ! Chrome not found — skipping PDF", file=sys.stderr)
        return False
    cmd = [
        chrome,
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        "--no-pdf-header-footer",
        "--virtual-time-budget=4000",
        f"--print-to-pdf={pdf_path}",
        html_path.as_uri(),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0 or not pdf_path.exists():
        print(f"  ! Chrome failed: {proc.stderr.strip()[:400]}", file=sys.stderr)
        return False
    return True


# --------------------------------------------------------------------------

def build(lang: str, paper: str | None, skip_pdf: bool) -> dict:
    src = CONTENT / f"cv.{lang}.toml"
    if not src.exists():
        sys.exit(f"missing content file: {src}")
    cv = tomllib.loads(src.read_text(encoding="utf-8"))
    css = (TEMPLATE / "cv.css").read_text(encoding="utf-8")
    chosen_paper = paper or cv.get("meta", {}).get("paper", "letter")

    DIST.mkdir(exist_ok=True)
    html_path = DIST / f"cv.{lang}.html"
    html_path.write_text(render(cv, css, chosen_paper), encoding="utf-8")
    print(f"  → {html_path.relative_to(ROOT)}")

    if not skip_pdf:
        pdf_path = DIST / f"cv.{lang}.pdf"
        if to_pdf(html_path, pdf_path):
            size = pdf_path.stat().st_size // 1024
            pages = page_count(pdf_path)
            note = "" if pages <= 2 else "   ← over two pages, trim something"
            print(f"  → {pdf_path.relative_to(ROOT)} "
                  f"({pages} page{'s' if pages != 1 else ''}, {size} KB, "
                  f"{chosen_paper}){note}")

    return cv


def render_index(langs: list[str], cv_by_lang: dict, accent: str) -> str:
    """Landing page for GitHub Pages: pick a language, read or download."""
    name = next(iter(cv_by_lang.values()))["profile"]["name"]
    names = {"en": "English", "fr": "Français"}
    rows = "".join(
        f"""
    <li>
      <span class="lang">{esc(names.get(l, l))}</span>
      <span class="links">
        <a href="cv.{l}.html">read</a>
        <a href="cv.{l}.pdf">PDF</a>
      </span>
    </li>"""
        for l in langs
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(name)} — CV</title>
<style>
:root {{ --accent: {accent}; --ink: #16191c; --muted: #58626c; --rule: #e3e7ea; }}
* {{ box-sizing: border-box; }}
body {{
  margin: 0; min-height: 100vh; display: flex; align-items: center;
  justify-content: center; background: #e8eaec; color: var(--ink);
  font: 10.5pt/1.5 "Avenir Next", "Segoe UI", system-ui, -apple-system, sans-serif;
  padding: 24px;
}}
.card {{ background: #fff; padding: 40px 44px; max-width: 420px; width: 100%;
  box-shadow: 0 1px 3px rgba(0,0,0,.12), 0 12px 40px rgba(0,0,0,.10); }}
h1 {{ margin: 0; font-size: 20pt; font-weight: 600; letter-spacing: -.025em; }}
.role {{ margin: 6px 0 0; color: var(--accent); font-weight: 500; }}
ul {{ list-style: none; margin: 26px 0 0; padding: 0; }}
li {{ display: flex; justify-content: space-between; align-items: baseline;
  padding: 11px 0; border-top: 1px solid var(--rule); }}
.lang {{ font-weight: 500; }}
.links a {{ font-family: "SF Mono", Menlo, Consolas, monospace; font-size: 8.5pt;
  color: var(--muted); text-decoration: none; border-bottom: 1px solid var(--rule);
  margin-left: 14px; }}
.links a:hover {{ color: var(--accent); border-bottom-color: var(--accent); }}
</style>
</head>
<body>
<main class="card">
  <h1>{esc(name)}</h1>
  <p class="role">{rich(cv_by_lang.get('en', next(iter(cv_by_lang.values())))['profile']['headline'])}</p>
  <ul>{rows}</ul>
</main>
</body>
</html>
"""


def main() -> None:
    ap = argparse.ArgumentParser(description="Build the CV.")
    ap.add_argument("langs", nargs="*", default=None,
                    help="language codes to build (default: every content file)")
    ap.add_argument("--paper", choices=["letter", "a4"],
                    help="override the paper size from [meta]")
    ap.add_argument("--html-only", action="store_true", help="skip PDF generation")
    args = ap.parse_args()

    langs = args.langs or sorted(
        p.name.split(".")[1] for p in CONTENT.glob("cv.*.toml")
    )
    built = {}
    for lang in langs:
        print(f"{lang}:")
        built[lang] = build(lang, args.paper, args.html_only)

    if built:
        accent = next(iter(built.values())).get("meta", {}).get("accent", "#0e5a63")
        index = DIST / "index.html"
        index.write_text(render_index(langs, built, accent), encoding="utf-8")
        print(f"index:\n  \u2192 {index.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
