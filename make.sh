#!/usr/bin/env bash

# Assumptions:
# 1. shell-escape version of rubber is installed
#    bzr branch lp:~brotchie/rubber/shell-escape
#    which had to be edited: set LoadClassWithOptions hook to 'oa' (because of ucithesis.cls)
# 2. have the python.sty package
#     hg clone https://bitbucket.org/brotchie/python-sty
#     ln -s python-sty/python.sty

mkdir -p output
cp *.py output/
touch thesis.tex
/usr/local/bin/rubber --pdf --shell-escape --into=output thesis.tex

