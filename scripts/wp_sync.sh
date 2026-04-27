#!/bin/bash

set -a
source /home/openclaw/insightginie/.env
set +a

/usr/bin/python3 /home/openclaw/insightginie/scripts/sync_wordpress.py
/usr/bin/python3 /home/openclaw/insightginie/scripts/sync_notion.py

cd /home/openclaw/insightginie || exit 1

git add .
git commit -m "auto sync $(date)" || true
git push