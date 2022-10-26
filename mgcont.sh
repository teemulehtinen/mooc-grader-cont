#!/bin/bash
OUT=$(python3 -m mgcont $@)
RES=$?
NAME=$(echo "$OUT" | tail -1)
echo "$OUT"
if [ "$RES" == 0 ] && [[ ${NAME} != *" "* ]]; then
  docker attach $NAME
fi
