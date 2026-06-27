# Docker — Guía básica de soporte técnico

## ¿Qué es Docker?

Docker es una plataforma que permite empaquetar aplicaciones junto con sus dependencias en unidades llamadas contenedores. Un contenedor se ejecuta de forma aislada en el sistema operativo del host, lo que facilita desplegar software de manera consistente en distintos entornos.

## ¿Qué es una imagen Docker?

Una imagen Docker es una plantilla de solo lectura que contiene el sistema de archivos, las librerías y la configuración necesaria para ejecutar una aplicación. Las imágenes son la base a partir de la cual se crean los contenedores.

## Crear una imagen Docker

Para construir una imagen a partir de un `Dockerfile` en el directorio actual:

```bash
docker build -t nombre-imagen .
```

- `-t nombre-imagen` asigna un nombre (tag) a la imagen.
- `.` indica que el contexto de construcción es el directorio actual.

## Ejecutar un contenedor

Para iniciar un contenedor a partir de una imagen y mapear el puerto 8080 del host al puerto 80 del contenedor:

```bash
docker run -p 8080:80 nombre-imagen
```

- `-p 8080:80` publica el puerto 80 interno del contenedor en el puerto 8080 del equipo local.

## ¿Qué es Docker Compose?

Docker Compose es una herramienta para definir y ejecutar aplicaciones multi-contenedor mediante un archivo YAML (`docker-compose.yml`). Permite describir servicios, redes y volúmenes en un solo archivo.

## Cuándo usar Docker Compose

Use Docker Compose cuando la aplicación requiere varios servicios que deben iniciarse juntos. Por ejemplo:

- Una API backend y una base de datos PostgreSQL.
- Un frontend, un backend y un servicio de caché Redis.

En lugar de ejecutar cada contenedor manualmente, Compose los levanta con un solo comando:

```bash
docker compose up
```
