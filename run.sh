#!/bin/bash
if [ DEPLOY_ENV == "PROD" ]; then
  gunicorn app:app -b 0.0.0.0:5000
else
  python app.py
fi
