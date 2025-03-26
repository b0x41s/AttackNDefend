#!/bin/bash
cd /app  # Zorg dat we in /app werken
service ssh start
python app.py
