#!/bin/sh

find . -maxdepth 1 -type f -iname "*" -printf "http://lmimagenes.sytes.net/memes/%f\n"|sort > memessud.csv
