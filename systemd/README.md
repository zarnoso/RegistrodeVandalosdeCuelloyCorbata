# Configuración systemd para Worker de Noticias

## Instalar:

```bash
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
