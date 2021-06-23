#!/bin/sh

find . -maxdepth 1 -type f -iname "*" -printf "http://lmimagenes.sytes.net/enghumor70/%f\n"|sort > humorsud.csv
