# Linux — Comandos básicos de soporte técnico

## Comandos básicos de archivos y directorios

| Comando | Descripción |
|---------|-------------|
| `ls` | Lista archivos y carpetas del directorio actual |
| `cd` | Cambia al directorio indicado |
| `mkdir` | Crea una nueva carpeta |
| `rm` | Elimina archivos o carpetas |

### Ejemplos

```bash
ls                  # ver contenido del directorio actual
cd /var/log         # entrar a la carpeta de logs
mkdir respaldos     # crear carpeta respaldos
rm archivo.txt      # eliminar un archivo
```

## Precaución con rm

El comando `rm` elimina archivos de forma permanente. Use `rm -r` con cuidado, ya que borra carpetas completas y su contenido. Antes de eliminar, confirme la ruta con `ls` o `pwd`.

## Ver procesos activos

Para listar los procesos en ejecución:

```bash
ps aux
```

Para monitorizar procesos en tiempo real:

```bash
top
```

`ps aux` muestra una instantánea de todos los procesos. `top` actualiza la información de forma continua y permite identificar procesos que consumen muchos recursos.

## Revisar uso de disco

Para ver el espacio disponible en las particiones del sistema:

```bash
df -h
```

La opción `-h` muestra los tamaños en formato legible (KB, MB, GB).

## Revisar archivos en una carpeta

Para explorar el contenido de un directorio:

```bash
ls -la /ruta/de/la/carpeta
```

- `-l` muestra detalles (permisos, tamaño, fecha).
- `-a` incluye archivos ocultos.

También puede usar `du -sh /ruta/de/la/carpeta` para conocer el tamaño total de una carpeta.
