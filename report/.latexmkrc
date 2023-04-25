ensure_path( 'TEXINPUTS', 'diploma-latex-template/diploma//');
$pdflatex = 'xelatex -synctex=1 -interaction=nonstopmode -shell-escape %O %S';