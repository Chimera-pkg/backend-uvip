# 🚀 Tutorial Deploy UVIP Backend ke VPS

**Target:** Deploy tanpa nabrak project lain yang sudah ada di VPS

---

## 📋 Persiapan

### Yang Sudah Ada di VPS
- ✅ Ubuntu 22.04/24.04
- ✅ Docker & Docker Compose
- ✅ Nginx (reverse proxy)
- ✅ Multiple project lain (kita akan isolasi total)

### Yang Akan Kita Buat
- 🐳 Docker Compose stack **terisolasi** (network `uvip_net`, prefix `uvip-`)
- 🗄️ PostgreSQL + PostGIS di container sendiri (port 5433 di host)
- 🚀 FastAPI app di container (port 8001 di host)
- 🌐 Nginx config baru (tidak ganggu config yang ada)

---

## 🎯 Langkah 1: Transfer Project ke VPS

### Opsi A: Via Git (Recommended)

```bash
# Di VPS
cd /opt  # atau /var/www, /home/ubuntu, dll
sudo git clone https://github.com/username/backend-uvip.git uvip-backend
cd uvip-backend
```

### Opsi B: Via SCP/SFTP

```bash
# Di komputer lokal
scp -r backend-uvip/ user@vps-ip:/opt/uvip-backend

# Atau pakai WinSCP/FileZilla
```

### Opsi C: Via Zip

```bash
# Di komputer lokal, zip project
cd backend-uvip
zip -r ../uvip-backend.zip . -x "venv/*" "__pycache__/*" "*.pyc" ".git/*"

# Upload ke VPS
scp ../uvip-backend.zip user@vps-ip:/opt/

# Di VPS, extract
cd /opt
sudo unzip uvip-backend.zip -d uvip-backend
cd uvip-backend
```

---

## 🔐 Langkah 2: Setup Environment Variables

```bash
cd /opt/uvip-backend

# Copy template .env
cp deploy/.env.example .env

# Edit .env dengan nano/vim
nano .env
```

**Isi file `.env`:**

```bash
# ---- Database Password ----
# GANTI dengan password yang kuat (minimal 16 karakter)
DB_PASSWORD=YourStrongPasswordHere2026!

# ---- JWT Secret Key ----
# Generate random string dengan command ini:
# python3 -c "import secrets; print(secrets.token_urlsafe(64))"
SECRET_KEY=paste_random_string_yang_panjang_disini

# ---- Token Expiry ----
ACCESS_TOKEN_EXPIRE_MINUTES=120
```

**Generate SECRET_KEY:**

```bash
# Jalankan di VPS
python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# Copy output-nya ke .env
```

**PENTING:**
- ❌ JANGAN commit `.env` ke Git
- ✅ `.env` sudah ada di `.gitignore`
- ✅ Backup `.env` di tempat aman (password manager)

---

## 🐳 Langkah 3: Build & Start Docker Containers

```bash
cd /opt/uvip-backend

# Build images (pertama kali, agak lama ~5-10 menit)
docker compose build

# Start semua containers di background
docker compose up -d

# Cek status
docker compose ps
```

**Expected output:**

```
NAME         IMAGE                  COMMAND                  SERVICE   PORTS
uvip-app     uvip-backend-app       "uvicorn main:app --…"   app       127.0.0.1:8001->8000/tcp
uvip-db      postgis/postgis:16-3.4 "docker-entrypoint.s…"   db        127.0.0.1:5433->5432/tcp
```

### Cek Logs (Optional)

```bash
# Lihat semua logs
docker compose logs -f

# Lihat logs app saja
docker compose logs -f app

# Lihat logs database saja
docker compose logs -f db

# Tekan Ctrl+C untuk keluar
```

---

## 🗄️ Langkah 4: Initialize Database

```bash
# Jalankan script init_db.py di dalam container app
docker compose exec app python init_db.py
```

**Expected output:**

```
🔧 Creating database tables...
✅ All tables created successfully!
📋 Tables in database (15):
   - users
   - corridors
   - survey_missions
   - mission_assignments
   - street_photos
   - segmentation_results
   - perception_predictions
   - shap_values
   - simulation_sessions
   - simulation_results
   - policy_recommendations
   - offline_sync_queue
   - batch_upload_jobs
   - model_registry
```

---

## 🌐 Langkah 5: Setup Nginx Reverse Proxy

### 5.1 Copy Config Nginx

```bash
# Copy config ke Nginx
sudo cp deploy/nginx-uvip.conf /etc/nginx/sites-available/uvip

# Buat symlink ke sites-enabled
sudo ln -s /etc/nginx/sites-available/uvip /etc/nginx/sites-enabled/uvip
```

### 5.2 Test & Reload Nginx

```bash
# Test config (wajib!)
sudo nginx -t

# Expected output:
# nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
# nginx: configuration file /etc/nginx/nginx.conf test is successful

# Reload Nginx (tidak restart, jadi tidak down)
sudo systemctl reload nginx
```

### 5.3 Verifikasi Nginx Config

```bash
# Cek apakah config sudah aktif
ls -la /etc/nginx/sites-enabled/ | grep uvip

# Cek Nginx status
sudo systemctl status nginx
```

---

## ✅ Langkah 6: Test API

### 6.1 Test via Docker (Internal)

```bash
# Test dari dalam VPS
curl http://127.0.0.1:8001/

# Expected:
# {"message":"UVIP API Online"}
```

### 6.2 Test via Nginx (External)

```bash
# Dari komputer lokal, buka browser:
http://VPS_IP:8001/

# Expected:
# {"message":"UVIP API Online"}
```

### 6.3 Test API Docs

```bash
# Swagger UI
http://VPS_IP:8001/docs

# ReDoc
http://VPS_IP:8001/redoc

# Custom API Docs
http://VPS_IP:8001/api-docs
```

### 6.4 Test Register User

```bash
# Test register admin
curl -X POST http://VPS_IP:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Admin UVIP",
    "email": "admin@uvip.id",
    "password": "admin123",
    "role": "admin"
  }'

# Expected: 201 Created dengan data user
```

---

## 🔧 Manajemen Daily

### Lihat Status Containers

```bash
cd /opt/uvip-backend
docker compose ps
```

### Restart Services

```bash
# Restart semua
docker compose restart

# Restart app saja
docker compose restart app

# Restart db saja
docker compose restart db
```

### Stop Services

```bash
# Stop semua (data tetap aman di volumes)
docker compose down

# Stop + hapus volumes (HATI-HATI! Data hilang!)
docker compose down -v
```

### Update Code

```bash
cd /opt/uvip-backend

# Pull perubahan dari Git
git pull origin main

# Rebuild app
docker compose build app

# Restart dengan image baru
docker compose up -d

# Database tetap aman (data di volume)
```

### Backup Database

```bash
# Backup database ke file SQL
docker compose exec db pg_dump -U uvip uvip > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore dari backup
cat backup_20260809_120000.sql | docker compose exec -T db psql -U uvip uvip
```

### Backup Uploads

```bash
# Upload files ada di Docker volume "uvip_uploads"
# Backup dengan:
docker run --rm -v uvip_uploads:/data -v $(pwd):/backup alpine \
  tar czf /backup/uploads_backup_$(date +%Y%m%d_%H%M%S).tar.gz -C /data .
```

### Lihat Logs

```bash
# Semua logs
docker compose logs -f

# App logs saja
docker compose logs -f app

# Database logs saja
docker compose logs -f db

# Last 100 lines
docker compose logs --tail=100 app
```

### Masuk ke Container (Debugging)

```bash
# Masuk ke app container
docker compose exec app bash

# Masuk ke database
docker compose exec db psql -U uvip uvip

# Keluar: exit
```

---

## 🔥 Firewall (Optional)

Kalau mau batasi akses ke port 8001:

```bash
# Cek status UFW
sudo ufw status

# Allow port 8001 (API)
sudo ufw allow 8001/tcp

# Kalau mau batasi IP tertentu saja:
# sudo ufw allow from YOUR_IP to any port 8001

# Reload firewall
sudo ufw reload
```

---

## 📊 Monitoring & Troubleshooting

### Cek Resource Usage

```bash
# Docker stats (CPU, RAM, Network)
docker stats

# Cek disk usage
docker system df

# Cek volume size
docker system df -v
```

### Problem: App Tidak Bisa Connect ke Database

```bash
# Cek apakah db container jalan
docker compose ps db

# Cek logs db
docker compose logs db

# Test connection dari app container
docker compose exec app python -c "
from app.db.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('✅ Database connected!', result.fetchone())
"
```

### Problem: Port Already in Use

```bash
# Cek siapa yang pakai port 8001
sudo lsof -i :8001

# Kalau ada process lain, stop dulu atau ganti port di docker-compose.yml
```

### Problem: Nginx 502 Bad Gateway

```bash
# Cek apakah app container jalan
docker compose ps app

# Cek logs app
docker compose logs app

# Restart app
docker compose restart app
```

### Problem: Database Tables Belum Dibuat

```bash
# Jalankan lagi init_db.py
docker compose exec app python init_db.py
```

---

## 🎓 Penjelasan Isolasi

### Kenapa Tidak Nabrak Project Lain?

1. **Docker Network Terisolasi**
   - Network name: `uvip_net`
   - Containers UVIP hanya bisa komunikasi sesama mereka
   - Tidak ganggu network project lain

2. **Port Binding ke localhost**
   - App: `127.0.0.1:8001` (hanya bisa diakses dari VPS itself)
   - DB: `127.0.0.1:5433` (hanya bisa diakses dari VPS itself)
   - Nginx yang expose ke public

3. **Docker Volumes Terpisah**
   - `uvip_pgdata` — database UVIP saja
   - `uvip_uploads` — uploads UVIP saja
   - Tidak campur dengan volume project lain

4. **Container Names dengan Prefix**
   - `uvip-app`, `uvip-db`
   - Mudah diidentifikasi, tidak bingung dengan container lain

5. **Nginx Config Terpisah**
   - File config: `/etc/nginx/sites-available/uvip`
   - Logs terpisah: `/var/log/nginx/uvip_access.log`
   - Tidak ganggu config site lain

---

## 📝 Checklist Deploy

- [ ] Transfer project ke VPS
- [ ] Setup `.env` dengan password & secret key yang kuat
- [ ] `docker compose build`
- [ ] `docker compose up -d`
- [ ] `docker compose exec app python init_db.py`
- [ ] Copy Nginx config ke `/etc/nginx/sites-available/uvip`
- [ ] `sudo ln -s /etc/nginx/sites-available/uvip /etc/nginx/sites-enabled/uvip`
- [ ] `sudo nginx -t`
- [ ] `sudo systemctl reload nginx`
- [ ] Test API: `curl http://VPS_IP:8001/`
- [ ] Test Swagger UI: `http://VPS_IP:8001/docs`
- [ ] Test register user

---

## 🔐 Security Recommendations

1. **Ganti Password Database**
   - Default di `.env.example` hanya contoh
   - Gunakan password minimal 16 karakter

2. **Ganti SECRET_KEY**
   - Generate dengan `python3 -c "import secrets; print(secrets.token_urlsafe(64))"`
   - JANGAN pakai yang sama dengan project lain

3. **Backup Rutin**
   - Database: setiap hari
   - Uploads: setiap minggu
   - Simpan di tempat berbeda (S3, Google Drive, dll)

4. **Update Dependencies**
   - Rutin cek `requirements.txt` untuk security updates
   - `docker compose build` setelah update

5. **Monitor Logs**
   - Cek logs secara berkala
   - Setup alert untuk error

6. **Firewall**
   - Batasi akses port 8001 ke IP tertentu kalau memungkinkan
   - Jangan expose port 5433 ke public

7. **HTTPS (Optional)**
   - Kalau mau pakai HTTPS, setup Let's Encrypt + Certbot
   - Atau pakai Cloudflare sebagai reverse proxy

---

## 🎉 Selesai!

API UVIP sudah jalan di:
- **API Root:** `http://VPS_IP:8001/`
- **Swagger UI:** `http://VPS_IP:8001/docs`
- **ReDoc:** `http://VPS_IP:8001/redoc`
- **Custom Docs:** `http://VPS_IP:8001/api-docs`

**Semua terisolasi dan tidak nabrak project lain!** 🚀
