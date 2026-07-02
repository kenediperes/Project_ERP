# Jalankan containers di background
docker compose up -d

# Lihat logs
docker compose logs -f odoo

# Cek status containers
docker compose ps

# Hentikan containers
docker compose stop

# Hentikan dan hapus containers (data tetap ada di volumes)
docker compose down

# Hentikan, hapus containers dan volumes (HATI-HATI: menghapus data)
docker compose down -v