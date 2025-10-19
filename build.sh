#!/usr/bin/env bash
# Dừng script nếu có lỗi
set -o errexit

# Cài đặt dependencies
pip install -r requirements.txt

# Thu thập static files mà không hỏi lại
python manage.py collectstatic --no-input

# Tạo migrations nếu có thay đổi trong models
python manage.py makemigrations --noinput

# Áp dụng các migrations vào database
python manage.py migrate --noinput
