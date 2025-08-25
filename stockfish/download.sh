#!/bin/bash

# See https://stockfishchess.org/download/
URL="https://github.com/official-stockfish/Stockfish/\
releases/download/sf_16/stockfish-ubuntu-x86-64-modern.tar"

DESTINATION_FOLDER="stockfish/"

# Download tarball and place in stockfish folder
mkdir -p "$DESTINATION_FOLDER"
curl -L "$URL" -o "${DESTINATION_FOLDER}stockfish-ubuntu-x86-64-modern.tar"

# Extract binary and delete tarball
tar -xf "$DESTINATION_FOLDER/stockfish-ubuntu-x86-64-modern.tar" \
--strip-components=1 \
--wildcards "*/stockfish-ubuntu-x86-64-modern"

mv stockfish-ubuntu-x86-64-modern "$DESTINATION_FOLDER"

rm "$DESTINATION_FOLDER/stockfish-ubuntu-x86-64-modern.tar"
