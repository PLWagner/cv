# Working in this repository

A bilingual CV built from one TOML file per language. `build.py` renders the
HTML and prints the PDF with headless Chrome; GitHub Actions publishes the
result to Pages.

## Build

```bash
make          # both languages, HTML + PDF
make html     # skip the PDF step while editing content
```

`make` prints the page count for each PDF.

## Rules that matter here

**Two pages, per language.** The build warns when a CV goes over, and CI
refuses to deploy. When one goes over, reach for `base_pt` in the `[meta]`
table before cutting anything — it sets the body size for that language
alone, and French needs a smaller setting than English for the same content.

**Standard library only.** No Jinja, no PyYAML, no Puppeteer, no package
manager. A CV gets touched twice a year, and a virtualenv or a `node_modules`
will be broken by then. TOML is read with `tomllib`, which ships with Python.
If something seems to need a dependency, vendor it instead.

**Sections lay out with floats, not CSS grid.** Chrome does not fragment a
grid container across a page break, so a long section gets pushed whole and
silently costs an entire page. Grid and flex are fine for small units that
never need to split — the impact tiles, a title-and-date row.

**One line per commit message.** Subject only, no body. Reasoning that needs
keeping goes in a comment next to the thing it explains.

## Editing content

Everything person-specific lives in `content/`. `template/cv.css` and
`build.py` carry no personal data.

Both language files should describe the same facts. They are adaptations
rather than translations, so wording diverges on purpose — but a change to a
date, a figure or a job title belongs in both.

In `bullets` and `context`, `**bold**` and `` `mono` `` are the only markup.

The French file sets its own punctuation conventions in a comment at the top.
Follow them; they are deliberate.

## Checking a change

Page count is the ground truth and comes straight out of the PDF:

```python
len(re.findall(rb"/Type\s*/Page[^s]", pdf_bytes))
```

To see where the height is going before a rebuild, open `dist/cv.en.html`,
force `.sheet` to the print content width — Letter minus 15 mm side margins —
and measure. Two pages is roughly 1900 px at 96 dpi. Leave real headroom:
elements that cannot split push past a page boundary, so a document that
measures just under the budget can still print three pages.
