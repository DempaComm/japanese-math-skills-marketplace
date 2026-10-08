#!/bin/zsh
cd "$(dirname "$0")"
exec python3 viewer/serve.py
