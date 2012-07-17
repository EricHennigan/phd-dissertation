PROJ = thesis

DEP	= thesis.tex

OUT = output

PDF	= $(OUT)/$(PROJ).pdf

LATEX = pdflatex -output-directory=$(OUT) -file-line-error

PDFVIEWER = open

.PHONY	: tex bib clean $(PDF)

$(PDF) : $(DEP)
	make tex

tex	:
	mkdir -p $(OUT)
	touch $(OUT)/$(PROJ).log
	while ($(LATEX) $(PROJ).tex ; \
		grep -q "Rerun to get cross" $(OUT)/$(PROJ).log ) do true ; \
		done

all :
	make tex
	make bib
	make tex
	make tex    # Run LaTeX again to make sure all references are correct

bib	:
	cp $(PROJ).bib $(OUT)
	cd $(OUT); bibtex $(PROJ); cd ..

show	: $(PDF)
	$(PDFVIEWER) "$(PDF)"

clean	:
	rm -rf $(OUT)
