#!/usr/bin/env bash
# Clone (or update) the public mal-lang repositories indexed by the RAG into sources/.
# Usage: ./fetchSources.sh
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"
mkdir -p sources

REPOS=(
  "exampleLang|https://github.com/mal-lang/exampleLang.git"
  "malcompiler|https://github.com/mal-lang/malcompiler.git"
  "mal-lang.github.io|https://github.com/mal-lang/mal-lang.github.io.git"
  "mal-specification|https://github.com/mal-lang/mal-specification.git"
  "mal-specification-wiki|https://github.com/mal-lang/mal-specification.wiki.git"
  "mal-toolbox|https://github.com/mal-lang/mal-toolbox.git"
  "mal-tutorials|https://github.com/mal-lang/mal-tutorials.git"
)

for entry in "${REPOS[@]}"; do
  name="${entry%%|*}"
  url="${entry#*|}"
  dest="sources/$name"
  if [ -d "$dest/.git" ]; then
    echo "Updating $name"
    git -C "$dest" pull --ff-only
  else
    echo "Cloning $name"
    git clone --depth 1 "$url" "$dest"
  fi
done

echo "Done. Build the index with: python3 mal_rag.py build"
