#!/bin/bash
set -eux

dnf update -y
dnf install -y docker
systemctl enable docker
systemctl start docker
usermod -aG docker ec2-user || true
dnf install -y docker-compose-plugin

mkdir -p /opt/churn && cd /opt/churn

cat > /opt/churn/docker-compose.yml <<'YAML'
services:
  api:
    image: vessou/churn-api:latest
    restart: unless-stopped
    expose: ["8000"]

  web:
    image: vessou/churn-web:latest
    restart: unless-stopped
    expose: ["8501"]
    environment:
      - STREAMLIT_SERVER_HEADLESS=true
      - STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

  nginx:
    image: nginx:stable
    restart: unless-stopped
    ports: ["80:80"]
    volumes:
      - /opt/churn/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - api
      - web
YAML

cat > /opt/churn/nginx.conf <<'NGINX'
user nginx;
worker_processes auto;

events { worker_connections 1024; }

http {
  include       /etc/nginx/mime.types;
  default_type  application/octet-stream;
  sendfile on;
  keepalive_timeout 65;

  upstream api_upstream { server api:8000; }
  upstream web_upstream { server web:8501; }

  server {
    listen 80;

    location / {
      proxy_pass http://web_upstream;
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
      rewrite ^/api/?(.*)$ /$1 break;
      proxy_pass http://api_upstream;
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_set_header X-Forwarded-Proto $scheme;
    }
  }
}
NGINX

/usr/bin/docker compose -f /opt/churn/docker-compose.yml up -d
