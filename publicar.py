#!/usr/bin/env python3
"""
Publica los Resúmenes (generados por Claude Cowork) al sitio web.
- Lee Resumen_*.docx desde ~/Desktop/Noticias_DF/YYYY-MM-DD/
- Convierte cada uno a HTML con mammoth
- Copia a docs/ junto con el .docx descargable
- Genera docs/index.html con los últimos 7 días disponibles
- Hace git add + commit + push automático
"""

import os
import re
import shutil
import subprocess
import sys
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import mammoth
from scraper_df import CARPETA_SALIDA, fecha_a_texto

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(REPO_DIR, "docs")
DIAS_A_MOSTRAR = 7
DIAS_NOMBRE = ["Lunes", "Martes", "Miércoles", "Jueves",
               "Viernes", "Sábado", "Domingo"]


# ─── BÚSQUEDA DE RESÚMENES ────────────────────────────────────────────────────

def encontrar_resumenes():
    """Devuelve [(fecha, ruta_docx), ...] ordenado del más reciente al más antiguo."""
    resultados = []
    if not os.path.exists(CARPETA_SALIDA):
        print(f"⚠️  Carpeta no existe: {CARPETA_SALIDA}")
        return resultados

    for nombre in os.listdir(CARPETA_SALIDA):
        ruta_dia = os.path.join(CARPETA_SALIDA, nombre)
        if not os.path.isdir(ruta_dia):
            continue
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", nombre):
            continue
        try:
            fecha = datetime.strptime(nombre, "%Y-%m-%d")
        except ValueError:
            continue

        for archivo in os.listdir(ruta_dia):
            if archivo.lower().startswith("resumen") and archivo.lower().endswith(".docx"):
                resultados.append((fecha, os.path.join(ruta_dia, archivo)))
                break

    resultados.sort(key=lambda x: x[0], reverse=True)
    return resultados[:DIAS_A_MOSTRAR]


# ─── CONVERSIÓN DOCX → HTML ───────────────────────────────────────────────────

PAGINA_CSS = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --naranja:#E65000;--naranja-h:#ff6a1a;
  --bg:#fafafa;--card:#fff;--borde:#e5e7eb;
  --texto:#1f2937;--muted:#6b7280;--link:#0056b3;
}
body{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);
     color:var(--texto);line-height:1.7;padding:2rem 1rem}
.container{max-width:780px;margin:0 auto}
.nav-volver{display:inline-block;margin-bottom:1.5rem;color:var(--naranja);
            text-decoration:none;font-weight:600}
.nav-volver:hover{text-decoration:underline}
header{text-align:center;border-bottom:3px solid var(--naranja);
       padding-bottom:1.5rem;margin-bottom:2rem}
header h1{color:var(--naranja);font-size:1.8rem;margin-bottom:.3rem}
header .fecha{color:var(--muted);font-size:1.05rem}
.descargar{display:inline-block;background:var(--naranja);color:#fff;
           padding:.5rem 1rem;border-radius:6px;text-decoration:none;
           font-size:.9rem;font-weight:600;margin-top:.8rem}
.descargar:hover{background:var(--naranja-h)}
.contenido{background:var(--card);border:1px solid var(--borde);
           border-radius:10px;padding:2rem 2.2rem}
.contenido h1,.contenido h2,.contenido h3{color:var(--naranja);
                                          margin:1.5rem 0 .8rem}
.contenido h1{font-size:1.5rem}
.contenido h2{font-size:1.25rem;border-bottom:1px solid var(--borde);
              padding-bottom:.3rem}
.contenido h3{font-size:1.1rem}
.contenido p{margin-bottom:.9rem}
.contenido ul,.contenido ol{margin:.5rem 0 1rem 1.5rem}
.contenido li{margin-bottom:.4rem}
.contenido strong{color:#111827}
.contenido a{color:var(--link)}
.contenido table{border-collapse:collapse;margin:1rem 0;width:100%}
.contenido th,.contenido td{border:1px solid var(--borde);padding:.5rem .8rem;
                            text-align:left}
.contenido th{background:#f3f4f6}
footer{text-align:center;color:var(--muted);font-size:.85rem;
       margin-top:3rem;padding-top:1.5rem;border-top:1px solid var(--borde)}
@media(max-width:640px){
  body{padding:1rem .6rem}
  .contenido{padding:1.2rem 1.4rem}
}
"""


def convertir_docx_a_html_body(docx_path: str) -> str:
    """Convierte un .docx a HTML semántico (sin html/head/body wrappers)."""
    with open(docx_path, "rb") as f:
        result = mammoth.convert_to_html(f)
    return result.value


def renderizar_pagina_dia(fecha: datetime, html_body: str, docx_filename: str) -> str:
    """Envuelve el body convertido en una página HTML completa."""
    fecha_humana = fecha_a_texto(fecha)
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Resumen DF — {fecha_humana}</title>
<style>{PAGINA_CSS}</style>
</head>
<body>
<div class="container">
<a href="index.html" class="nav-volver">← Volver al índice</a>
<header>
  <h1>Resumen Diario Financiero</h1>
  <div class="fecha">{fecha_humana}</div>
  <a class="descargar" href="{docx_filename}" download>📄 Descargar Word</a>
</header>
<div class="contenido">
{html_body}
</div>
<footer>
  Generado por Claude Cowork · Fuente: <a href="https://www.df.cl">df.cl</a>
</footer>
</div>
</body>
</html>
"""


# ─── ÍNDICE ───────────────────────────────────────────────────────────────────

INDEX_CSS = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --naranja:#E65000;--naranja-h:#ff6a1a;
  --bg:#fafafa;--card:#fff;--borde:#e5e7eb;
  --texto:#1f2937;--muted:#6b7280;
}
body{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);
     color:var(--texto);line-height:1.6;padding:2rem 1rem;min-height:100vh}
.container{max-width:780px;margin:0 auto}
header{text-align:center;border-bottom:3px solid var(--naranja);
       padding-bottom:1.5rem;margin-bottom:2.5rem}
header h1{color:var(--naranja);font-size:2rem;margin-bottom:.4rem}
header .sub{color:var(--muted);font-size:1rem}
.intro{text-align:center;color:var(--muted);margin-bottom:2rem;font-size:.95rem}
.grid{display:flex;flex-direction:column;gap:.8rem}
.card{background:var(--card);border:1px solid var(--borde);border-radius:10px;
      padding:1.2rem 1.4rem;text-decoration:none;color:var(--texto);
      display:flex;justify-content:space-between;align-items:center;
      transition:all .15s ease;flex-wrap:wrap;gap:.8rem}
.card:hover{border-color:var(--naranja);transform:translateY(-2px);
            box-shadow:0 4px 12px rgba(230,80,0,.08)}
.card-fecha{display:flex;flex-direction:column;gap:.2rem}
.dia-semana{font-weight:bold;color:var(--naranja);font-size:1.1rem}
.fecha-completa{font-size:.9rem;color:var(--muted)}
.docx{color:var(--naranja);text-decoration:none;font-weight:600;font-size:.85rem}
.docx:hover{color:var(--naranja-h);text-decoration:underline}
.empty{text-align:center;color:var(--muted);padding:3rem 1rem;
       background:var(--card);border:1px dashed var(--borde);border-radius:10px}
footer{text-align:center;color:var(--muted);font-size:.85rem;
       margin-top:3rem;padding-top:1.5rem;border-top:1px solid var(--borde)}
footer a{color:var(--naranja);text-decoration:none}
@media(max-width:520px){
  body{padding:1rem .6rem}
  header h1{font-size:1.5rem}
  .card{padding:1rem}
}
"""


def generar_index(dias_publicados: list):
    """Construye docs/index.html con los días disponibles.
       dias_publicados es lista de (fecha, docx_filename)."""
    fecha_hoy_humana = fecha_a_texto(datetime.now())

    cards = []
    for fecha, docx_name in dias_publicados:
        fecha_iso = fecha.strftime("%Y-%m-%d")
        dia_sem = DIAS_NOMBRE[fecha.weekday()]
        cards.append(f"""
    <a class="card" href="{fecha_iso}.html">
      <div class="card-fecha">
        <span class="dia-semana">{dia_sem}</span>
        <span class="fecha-completa">{fecha_a_texto(fecha)}</span>
      </div>
      <a class="docx" href="{docx_name}" download
         onclick="event.stopPropagation()">📄 Word</a>
    </a>""")

    if not cards:
        cards.append(
            '<p class="empty">Aún no hay resúmenes disponibles.</p>'
        )

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Resumen Diario Financiero</title>
<style>{INDEX_CSS}</style>
</head>
<body>
<div class="container">
  <header>
    <h1>📰 Resumen Diario Financiero</h1>
    <div class="sub">Análisis diario del mercado chileno</div>
  </header>

  <p class="intro">Selecciona una fecha para ver el resumen del día. Disponibles los últimos {DIAS_A_MOSTRAR} días.</p>

  <div class="grid">
    {''.join(cards)}
  </div>

  <footer>
    Última actualización: {fecha_hoy_humana}<br>
    Fuente: <a href="https://www.df.cl">df.cl</a> · Análisis por Claude Cowork
  </footer>
</div>
</body>
</html>
"""

    with open(os.path.join(DOCS_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)


# ─── LIMPIEZA ─────────────────────────────────────────────────────────────────

def limpiar_docs(fechas_validas: set):
    """Borra de docs/ los archivos cuya fecha no está en fechas_validas."""
    if not os.path.exists(DOCS_DIR):
        return
    for archivo in os.listdir(DOCS_DIR):
        m = re.match(r"^(\d{4}-\d{2}-\d{2})\.(html|docx)$", archivo)
        if m and m.group(1) not in fechas_validas:
            try:
                os.remove(os.path.join(DOCS_DIR, archivo))
                print(f"  🗑️  eliminado: {archivo}")
            except Exception:
                pass


# ─── GIT ──────────────────────────────────────────────────────────────────────

def git(*args, check=True):
    """Ejecuta git desde REPO_DIR."""
    return subprocess.run(
        ["git", "-C", REPO_DIR] + list(args),
        check=check, capture_output=True, text=True, encoding="utf-8",
    )


def hay_repositorio_git() -> bool:
    r = git("rev-parse", "--is-inside-work-tree", check=False)
    return r.returncode == 0


def hay_remote_configurado() -> bool:
    r = git("remote", "get-url", "origin", check=False)
    return r.returncode == 0


def push_a_github():
    """Hace git pull --ff-only, add, commit y push. No falla si no hay cambios."""
    if not hay_repositorio_git():
        print("⚠️  No es un repositorio git. Saltando push.")
        return
    if not hay_remote_configurado():
        print("⚠️  No hay remote 'origin' configurado. Saltando push.")
        return

    # Sincronizar con remoto (por si pusheaste desde otro PC)
    r = git("pull", "--ff-only", check=False)
    if r.returncode != 0:
        print(f"⚠️  git pull --ff-only falló:\n{r.stderr}")
        print("   Continuando sin pull. Si hay conflicto, el push fallará.")

    git("add", "docs/")
    r = git("diff", "--staged", "--quiet", check=False)
    if r.returncode == 0:
        print("📭 Sin cambios en docs/. No hay nada que pushear.")
        return

    fecha = datetime.now().strftime("%Y-%m-%d")
    git("commit", "-m", f"Publicar resumen {fecha}")

    r = git("push", check=False)
    if r.returncode != 0:
        print(f"❌ git push falló:\n{r.stderr}")
        sys.exit(1)
    print("✅ Cambios pusheados a GitHub.")


# ─── FLUJO PRINCIPAL ──────────────────────────────────────────────────────────

def main():
    os.makedirs(DOCS_DIR, exist_ok=True)
    print(f"📁 Carpeta de resúmenes: {CARPETA_SALIDA}")
    print(f"📁 Carpeta del sitio:    {DOCS_DIR}\n")

    resumenes = encontrar_resumenes()
    if not resumenes:
        print("⚠️  No se encontraron archivos Resumen_*.docx.")
        print("   Verificar que Cowork ya haya generado al menos uno.")
        # Aún así genera un index vacío y sale
        generar_index([])
        return

    print(f"✅ {len(resumenes)} resumen(es) encontrado(s):")
    publicados = []
    for fecha, docx_path in resumenes:
        fecha_iso = fecha.strftime("%Y-%m-%d")
        docx_dest = f"{fecha_iso}.docx"
        html_dest = f"{fecha_iso}.html"
        print(f"   - {fecha_iso}: {os.path.basename(docx_path)}")

        try:
            html_body = convertir_docx_a_html_body(docx_path)
            pagina = renderizar_pagina_dia(fecha, html_body, docx_dest)
        except Exception as e:
            print(f"     ❌ Error convirtiendo: {e}")
            continue

        with open(os.path.join(DOCS_DIR, html_dest), "w", encoding="utf-8") as f:
            f.write(pagina)
        shutil.copy2(docx_path, os.path.join(DOCS_DIR, docx_dest))
        publicados.append((fecha, docx_dest))

    fechas_validas = {f.strftime("%Y-%m-%d") for f, _ in publicados}
    limpiar_docs(fechas_validas)
    generar_index(publicados)

    print(f"\n🌐 Sitio generado: {os.path.join(DOCS_DIR, 'index.html')}")
    print("\n🚀 Pusheando a GitHub...")
    push_a_github()


if __name__ == "__main__":
    main()
