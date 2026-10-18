# CV — build targets. Needs Python 3.11+ and Google Chrome, nothing else.
PAPER ?=
PAPERFLAG := $(if $(PAPER),--paper $(PAPER),)

.PHONY: all en fr html open clean

all:              ## Build HTML + PDF for every language
	@python3 build.py $(PAPERFLAG)

en:               ## English only
	@python3 build.py en $(PAPERFLAG)

fr:               ## French only
	@python3 build.py fr $(PAPERFLAG)

html:             ## HTML only — fast loop while editing content
	@python3 build.py --html-only

open: all         ## Build, then open both PDFs
	@open dist/cv.en.pdf dist/cv.fr.pdf

clean:            ## Remove build output
	@rm -f dist/cv.*.html dist/cv.*.pdf
