# Cómo publicar los resúmenes en una web pública

Pasos para publicar los `Resumen_*.docx` (los que genera Cowork) en una URL
tipo `https://TU-USUARIO.github.io/noticias-df/` que cualquiera pueda ver.

El sitio se actualiza solo cada día a las 11:30 (10 min después de Cowork),
desde tu PC. Si tu PC está apagado ese día, simplemente queda el último
resumen publicado y se actualiza la próxima vez que se prenda al mediodía.

---

## Cómo funciona el flujo completo

```
11:15 → tarea programada "ScraperDiarioFinanciero" → genera 2026-04-30_DF.docx
11:20 → Cowork lee el .docx y genera Resumen_2026-04-30.docx
11:30 → tarea programada "PublicarResumenDF" → ejecuta publicar.py:
          1. Lee los Resumen_*.docx de los últimos 7 días
          2. Los convierte a HTML
          3. Genera docs/index.html con la lista
          4. Hace git push a GitHub
11:31 → GitHub Pages publica automáticamente la nueva versión
```

---

## Paso 1 — Probar localmente

Ya está probado y funciona. Si quieres volver a verlo:

```bash
cd "C:\Users\seba\Desktop\files"
python publicar.py
```

Debería decir "No es un repositorio git. Saltando push." (eso es normal antes
del Paso 3) y abrir `docs/index.html` te muestra el sitio.

---

## Paso 2 — Crear un repositorio en GitHub

1. Entra a https://github.com/new
2. **Repository name**: `noticias-df` (o el nombre que quieras)
3. Marca **Public** (debe ser público para usar GitHub Pages gratis)
4. **NO** marques "Add a README", ni .gitignore, ni licencia.
5. Click **Create repository**.
6. Anota la URL del repo: `https://github.com/TU-USUARIO/noticias-df.git`.

---

## Paso 3 — Subir el código por primera vez

Abre una terminal (PowerShell o CMD) en `C:\Users\seba\Desktop\files`:

```bash
git init
git add .
git commit -m "Versión inicial"
git branch -M main
git remote add origin https://github.com/TU-USUARIO/noticias-df.git
git push -u origin main
```

Cambia `TU-USUARIO` por tu usuario real de GitHub.

> **Si nunca configuraste git en este PC**, primero corre:
> ```bash
> git config --global user.name "Tu Nombre"
> git config --global user.email "sebagabler1@gmail.com"
> ```
>
> **Para autenticarte con GitHub** la primera vez que hagas `git push`,
> Windows abrirá una ventana de "Git Credential Manager" que te pedirá
> iniciar sesión con tu cuenta de GitHub en el navegador. Después queda
> guardado y no vuelve a preguntar.

---

## Paso 4 — Activar GitHub Pages

1. En el repo en GitHub: **Settings** → **Pages** (menú izquierdo).
2. En **Source**, elige **Deploy from a branch**.
3. En **Branch**, elige `main` y carpeta `/docs`. Click **Save**.
4. Espera 1–2 minutos. Refresca la página y arriba aparecerá:
   `Your site is live at https://TU-USUARIO.github.io/noticias-df/`

Listo. Esa es la URL pública.

---

## Paso 5 — Instalar la tarea programada

Doble click sobre **`instalar_publicacion.bat`**.

Esto crea una tarea de Windows que cada día a las **12:25** ejecuta
`publicar.bat`, que a su vez:
1. Convierte el Resumen del día a HTML
2. Lo agrega al sitio
3. Hace `git push` automático

> Si ves un error "No se pudo crear la tarea", click derecho sobre
> el .bat y elige **Ejecutar como administrador**.

---

## Listo

A partir de mañana, todos los días el sitio se actualizará solo. Comparte
la URL `https://TU-USUARIO.github.io/noticias-df/` con quien quieras.

---

## Cosas útiles

### Publicar a mano (sin esperar a las 12:25)

Doble click sobre **`publicar.bat`**, o desde una terminal:
```bash
python publicar.py
```

### Ver los logs de la publicación automática

Se guardan en `publicar.log` en esta misma carpeta.

### Si tu PC estuvo apagado el día anterior

No pasa nada. El sitio sigue mostrando el último resumen disponible. Cuando
prendas el PC, si Cowork ya generó el resumen del día anterior (manual o
porque lo configuraste así), la próxima ejecución de 12:25 lo subirá
automáticamente junto con el del día actual.

Si quieres forzar una publicación inmediata, doble click en `publicar.bat`.

### Desinstalar la tarea programada

```bash
schtasks /delete /tn "PublicarResumenDF" /f
```

### Cambiar la hora

Edita `instalar_publicacion.bat` la línea `/st 12:25` y vuelve a correrlo.

### Cambiar cuántos días se muestran

Edita `publicar.py`, la constante:
```python
DIAS_A_MOSTRAR = 7
```

---

## Si algo falla

- **`git push` falla con "Authentication failed"**: vuelve a abrir el Git
  Credential Manager. Suele pasar si la sesión expiró. Una corrida manual
  de `publicar.bat` te pedirá login otra vez.
- **El sitio no aparece**: revisar Paso 4. Pages tarda hasta 2 minutos en
  publicar la primera vez.
- **`publicar.log` tiene errores**: ábrelo y mándamelo.
