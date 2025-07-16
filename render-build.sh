#!/usr/bin/env bash

# Cài đặt yêu cầu với pip, tắt build isolation
pip install --no-build-isolation --upgrade pip
pip install --no-build-isolation -r requirements.txt

# Nếu bạn có app Flask thì chạy Flask:
# python main.py  hoặc gunicorn app:app
