#!/bin/bash

echo "🚀 Initializing ERP System with WhatsApp & Telegram Integration"
echo "================================================================"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Create directories
mkdir -p config addons services/whatsapp services/telegram services/celery nginx ssl

# Copy .env if not exists
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠️  Please edit .env file with your credentials"
fi

# Build and start services
echo "📦 Building Docker images..."
docker compose build

echo "🚀 Starting services..."
docker compose up -d

echo ""
echo "✅ ERP System is starting..."
echo ""
echo "📊 Access your ERP at: http://localhost:8069"
echo "🤖 Telegram Bot: Configure via Odoo settings"
echo "💬 WhatsApp: Scan QR code from logs"
echo ""
echo "To see logs:"
echo "  docker compose logs -f"
echo ""
echo "To view WhatsApp QR code:"
echo "  docker compose logs -f whatsapp-service"