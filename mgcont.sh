#!/bin/bash
cd $(dirname $0)
DIR=submission_tmp
if [ -d $DIR ]; then
  docker run --rm -v $(pwd):/wdir teemule/flask rm -rf /wdir/$DIR
fi
OUT=$(python3 -m mgcont $@$NARG)
RES=$?
NAME=$(echo "$OUT" | tail -1)
echo "$OUT"
if [ "$RES" == 0 ] && [[ ${NAME} != *" "* ]]; then
  docker attach $NAME
fi
