#!/bin/sh
usage() {
  printf 'Usage: %s path_to_backup path_to_restore\n' "$0" >&2; exit 1
}

[ "$1" = '-h' ] || [ "$2" = '-h' ] || [ "$1" = '--help' ] || [ "$2" = '--help' ] || [ "$#" -lt 2 ] && usage

xz --stdout --decompress "$1" > "$2" && printf "backup restored\n"
