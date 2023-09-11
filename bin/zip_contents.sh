#!/bin/bash
mkdir tozip/
cp "$1" tozip/
cp "$2" tozip/
cd tozip
zip "$3" *
cd ..
rm -rf tozip