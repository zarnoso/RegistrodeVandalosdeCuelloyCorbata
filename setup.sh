#!/bin/bash
# Script de instalación para Registro de Vándalos

set -e

echo "=== Instalando Registro de Vándalos ==="
echo ""

# 1. Crear entorno virtual
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✅ Entorno virtual creado"
fi

source .venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt > /dev/null
echo "✅ Dependencias instaladas"

# 3. Crear directorio de logs
mkdir -p logs

# 4. Instalar systemd (opcional)
if [ "$1" == "--install-systemd" ]; then
    if [ ! -f ".env" ]; then
        echo "❌ Falta el archivo .env con DATABASE_URL (y opcionalmente TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID)."
        echo "   Créalo antes de instalar systemd, ej:"
        echo "   echo 'DATABASE_URL=postgresql://usuario:password@host/db?sslmode=require' > .env"
        exit 1
    fi
    sudo cp systemd/worker-noticias.service /etc/systemd/system/
    sudo cp systemd/worker-noticias.timer /etc/systemd/system/
    sudo touch /var/log/worker-noticias.log
    sudo chown $USER:$USER /var/log/worker-noticias.log
    sudo systemctl daemon-reload
    sudo systemctl enable --now worker-noticias.timer
    echo "✅ Systemd timer instalado"
fi

# 5. Correr tests
echo ""
echo "=== Tests ==="
pytest tests/ -v || echo "⚠️ Tests fallaron"

echo ""
echo "=== Instalación completada ==="
echo ""
echo "Para iniciar el servidor:"
echo "  source .venv/bin/activate"
echo "  python3 backend.py"
