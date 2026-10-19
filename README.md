# CV — Pierre-Luc Wagner

A bilingual CV (EN / FR) built from one data file per language, versioned in
Git and published to GitHub Pages.

Nothing to install: Python 3.11+ (standard library only) and Google Chrome.

**Live:** https://plwagner.github.io/cv/

## Usage

```bash
make            # build HTML + PDF for every language into dist/
make en         # English only
make fr         # French only
make html       # HTML only, skip the PDF step
make open       # build, then open both PDFs
make clean
```

`make` prints the page count and warns when a CV goes over two pages.

## Layout

| Path                   | What it is |
|------------------------|------------|
| `content/cv.en.toml`   | English content |
| `content/cv.fr.toml`   | French content |
| `template/cv.css`      | All the styling, screen and print |
| `build.py`             | Reads the TOML, renders the HTML, prints the PDF |
| `dist/`                | Output — `index.html`, `cv.en.*`, `cv.fr.*` |
| `.github/workflows/`   | Build and deploy to GitHub Pages |

The HTML is self-contained: the CSS is inlined. Email it or host it as is.

## Making it yours

Fork it, then replace the two files in `content/`. Nothing else is
person-specific.

An entry looks like this:

```toml
[[experience]]
company  = "Employer"
role     = "Job title"
location = "City, Region"
start    = "2026"
end      = "present"
context  = "One line to set the scene and the scale."
bullets  = [
  "Something you did, with a **number** in it.",
  "Something else, with `terraform` set in mono.",
]
tech = ["GCP", "Kubernetes", "Terraform"]
```

Consecutive entries sharing a `company` are grouped under a single employer
heading, which is how you show a progression of titles at one place.

`**bold**` and `` `mono` `` work in `bullets` and `context`.

Drop a language by deleting its file in `content/`; add one by copying an
existing file and translating it. `build.py` picks up whatever is there.

## Holding two pages

Two pages is the target, and `make` tells you when you miss it. Before cutting
content, try `base_pt` in the `[meta]` table — it sets the body size for that
language alone. French runs about ten percent longer than English for the same
material, which is why it sits lower here.

## Publishing

`.github/workflows/pages.yml` builds and deploys on every push to `main`. It
refuses to deploy if a CV comes out over two pages or an expected file is
missing, so the length discipline is enforced by CI rather than by memory.

In the repository settings, set Pages → Source to **GitHub Actions**.

`dist/index.html` is a generated landing page: pick a language, read it online
or download the PDF.
