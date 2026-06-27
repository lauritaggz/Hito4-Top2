# Git — Guía básica de soporte técnico

## ¿Qué es Git?

Git es un sistema de control de versiones distribuido que permite registrar cambios en archivos de un proyecto, colaborar con otros desarrolladores y mantener un historial de modificaciones.

## Comandos esenciales

### git clone

Descarga una copia de un repositorio remoto al equipo local:

```bash
git clone https://github.com/usuario/proyecto.git
```

### git status

Muestra el estado del repositorio: archivos modificados, nuevos o preparados para commit.

```bash
git status
```

### git pull

Descarga e integra los cambios más recientes del repositorio remoto:

```bash
git pull
```

### git add

Marca archivos para incluirlos en el próximo commit:

```bash
git add archivo.txt
git add .
```

### git commit

Registra los cambios preparados con un mensaje descriptivo:

```bash
git commit -m "Descripción del cambio"
```

### git push

Envía los commits locales al repositorio remoto:

```bash
git push
```

## Cómo actualizar un repositorio

Siga estos pasos para actualizar su copia local:

1. Entrar a la carpeta del proyecto:
   ```bash
   cd /ruta/al/proyecto
   ```
2. Ejecutar `git status` para revisar el estado actual.
3. Ejecutar `git pull` para traer los cambios del remoto.
4. Revisar nuevamente con `git status` para confirmar que el repositorio está actualizado.

## Verificar cambios pendientes

Use `git status` para comprobar si tiene cambios sin confirmar. El comando indicará:

- Archivos modificados que aún no se han añadido (`git add`).
- Archivos en staging listos para commit.
- Archivos no rastreados (nuevos).

Si después de `git pull` aparecen conflictos o cambios locales, resuélvalos antes de continuar trabajando.
