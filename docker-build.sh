#!/bin/bash
set -o nounset -o errexit

readonly IMAGE_REPO="ghcr.io/freitagsrunde/dmarc-report-aggregator"
VERSION="$(python -c 'print(__import__("dmarc_report_aggregator").__version__)')"

PUSH=false
while getopts ":p" OPT; do
  case "$OPT" in
  p)
    PUSH=true
    ;;
  *)
    echo "usage: $0 [-p]" >&2
    exit 1
  esac
done

docker build "$(dirname "$0")" -t "$IMAGE_REPO:$VERSION" -t "$IMAGE_REPO:latest"

if $PUSH; then
  docker push "$IMAGE_REPO:$VERSION"
  docker push "$IMAGE_REPO:latest"
else
  echo "Built $VERSION locally. Use -p to push." >&2
fi
