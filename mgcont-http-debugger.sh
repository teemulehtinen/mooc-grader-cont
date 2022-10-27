#!/bin/bash
cd $(dirname $0)
NW=$(docker network ls | grep " mgcont " | wc -l)
if [ $NW -eq 0 ]; then
  docker network create mgcont
fi
docker run \
  --rm \
  --network mgcont \
  --network-alias debugger \
  -p 5000:5000 \
  -it \
  -v $(pwd)/server:/server \
  teemule/flask \
  python3 -m flask -A /server/DebugHTTPServer.py run -h 0.0.0.0
