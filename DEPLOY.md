# Oracle Cloud Free Tier Deployment Guide

## Step 1: Create Oracle Cloud Account
1. Go to https://cloud.oracle.com/
2. Sign up for Free Tier (needs credit card, not charged)
3. Create a **VM Instance** (ARM A1.Flex — always free, 4 OCPU, 24GB RAM)

## Step 2: SSH Into Your VM
```bash
# Download your SSH key from Oracle Cloud console
ssh -i your-key.pem opc@YOUR_ORACLE_PUBLIC_IP
```

## Step 3: Install Docker & Docker Compose
```bash
sudo dnf update -y
sudo dnf install -y docker docker-compose-plugin
sudo systemctl enable --now docker
sudo usermod -aG docker opc
newgrp docker
```

## Step 4: Clone Your Project
```bash
cd /home/opc
git clone https://github.com/Satendra90390/SMS-Pro.git
cd SMS-Pro
```

## Step 5: Create Production .env
```bash
cp .env.example .env
nano .env
```
Fill in real values:
- `DJANGO_SECRET_KEY` — run `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- `DEBUG=False`
- `ALLOWED_HOSTS=YOUR_ORACLE_PUBLIC_IP`
- `DB_PASSWORD` — a strong password for PostgreSQL
- Your Google/GitHub/Groq API keys

## Step 6: Open Firewall Ports
```bash
# Oracle Cloud: open ports 80 and 8000 in the security list (console)
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

## Step 7: Build & Run
```bash
docker compose up -d --build
```

## Step 8: Run Migrations & Create Admin
```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

## Step 9: Access Your App
Open: `http://YOUR_ORACLE_PUBLIC_IP:8000`

## Commands
```bash
# View logs
docker compose logs -f

# Restart
docker compose restart

# Stop
docker compose down

# Update after git pull
git pull
docker compose up -d --build
```

## Optional: Use Nginx for Port 80 + SSL
```bash
sudo dnf install -y nginx
# Configure nginx reverse proxy to 8000
# Add SSL with certbot for your domain
```
