# Configuración systemd para Worker de Noticias

## Instalar:

```bash
# Crear archivo de credenciales fuera del repo (NUNCA subir a git)
cat > /home/chumbeke/registro-devandalos/.env << 'EOF'
DATABASE_URL=postgresql://usuario:password@host/db?sslmode=require
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
EOF
chmod 600 /home/chumbeke/registro-devandalos/.env

# Copiar archivos systemd
sudo cp systemd/worker-noticias.service /etc/systemd/system/
sudo cp systemd/worker-noticias.timer /etc/systemd/system/

# Crear log file
sudo touch /var/log/worker-noticias.log
sudo chown chumbeke:chumbeke /var/log/worker-noticias.log

# Activar timer
sudo systemctl daemon-reload
sudo systemctl enable --now worker-noticias.timer
```

## Comandos útiles:

```bash
# Ver estado
systemctl status worker-noticias.timer

# Ver logs
journalctl -u worker-noticias.service -f

# Ejecutar manualmente
sudo systemctl start worker-noticias.service

# Ver próxima ejecución
systemctl list-timers
```

## Frecuencia:
- Diario a las 06:00 (hora de Chile / UTC-4)

## Alertas Telegram (opcional):

Editar el servicio systemd:

```bash
sudo systemctl edit worker-noticias.service
```

Agregar:
```
[Service]
Environment=TELEGRAM_BOT_TOKEN=tu_token
Environment=TELEGRAM_CHAT_ID=tu_chat_id
```

Obtener chat ID: habla con el bot y visita `https://api.telegram.org/bot<TOKEN>/getUpdates`
