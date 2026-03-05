#!/bin/bash

python3 scripts/api_server.py &
sleep 2
python3 scripts/main.py