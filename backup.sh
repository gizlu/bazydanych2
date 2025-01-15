#!/bin/sh
usage() {
  printf 'Usage: %s path_to_db\n' "$0" >&2; exit 1
}

[ "$1" = '-h' ] || [ "$1" = '--help' ] || [ "$#" -lt 1 ] && usage

out="$1.backup.$(date +%F_%R ).xz"
xz --stdout "$1" > "$out" && printf "backup saved as %s\n" "$out"
