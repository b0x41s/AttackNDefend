#!/bin/bash
/usr/sbin/sshd &  # Start SSH in de achtergrond
python app.py     # Start Flask-app in de voorgrond