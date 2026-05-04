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
import unicodedata
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import mammoth
from bs4 import BeautifulSoup
from scraper_df import CARPETA_SALIDA, fecha_a_texto

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(REPO_DIR, "docs")
DIAS_A_MOSTRAR = 7
DIAS_NOMBRE = ["Lunes", "Martes", "Miércoles", "Jueves",
               "Viernes", "Sábado", "Domingo"]

SECCIONES_DF = [
    ("Mercados",      "mercados"),
    ("Empresas",      "empresas"),
    ("Economía",      "economia"),
    ("Internacional", "internacional"),
    ("Innovación",    "innovacion"),
    ("Opinión",       "opinion"),
]


def render_sidebar(base_url: str = "") -> str:
    """Sidebar con las 6 secciones. Si base_url='', los hrefs son anchors
       relativos al documento actual. Si base_url='X.html', son deep-links."""
    items = []
    for nombre, slug in SECCIONES_DF:
        href = f"{base_url}#{slug}" if base_url else f"#{slug}"
        items.append(f'<li><a href="{href}">{nombre}</a></li>')
    return f"""
<aside class="sidebar">
  <div class="sidebar-titulo">📚 Por sección</div>
  <ul>{''.join(items)}</ul>
</aside>"""


SIDEBAR_CSS = """
.sidebar{position:fixed;left:1.5rem;top:1.5rem;width:185px;
        background:var(--card);border:1px solid var(--borde);
        border-radius:12px;padding:1rem 1.1rem;z-index:5;
        box-shadow:0 4px 12px rgba(0,0,0,.04)}
.sidebar-titulo{font-size:.72rem;font-weight:700;color:var(--naranja);
                text-transform:uppercase;letter-spacing:.1em;
                margin-bottom:.6rem;padding:0 .3rem}
.sidebar ul{list-style:none;padding:0;margin:0}
.sidebar li{margin:0}
.sidebar a{color:var(--texto);text-decoration:none;display:block;
          padding:.45rem .7rem;border-radius:7px;transition:all .15s;
          font-size:.92rem}
.sidebar a:hover{background:var(--naranja-soft);color:var(--naranja)}
.sidebar a.active{background:var(--naranja);color:#fff;font-weight:600}
@media(max-width:1140px){.sidebar{display:none}}
"""

THEME_INIT_JS = """
<script>
(function(){try{var t=localStorage.getItem('theme')||'light';document.documentElement.setAttribute('data-theme',t);}catch(e){}})();
function toggleTheme(){var h=document.documentElement;var n=h.getAttribute('data-theme')==='dark'?'light':'dark';h.setAttribute('data-theme',n);try{localStorage.setItem('theme',n);}catch(e){}}
</script>
"""

THEME_TOGGLE_HTML = """
<button class="theme-toggle" onclick="toggleTheme()" aria-label="Cambiar modo" title="Cambiar a modo noche / día">
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
    <path d="M9 18h6"/>
    <path d="M10 22h4"/>
    <path d="M12 2a7 7 0 0 0-4 12.7c1 .8 1.5 1.7 1.5 2.7v.6h5v-.6c0-1 .5-1.9 1.5-2.7A7 7 0 0 0 12 2z"/>
  </svg>
</button>
"""

THEME_CSS = """
.theme-toggle{position:fixed;top:1rem;right:1rem;z-index:100;
              width:44px;height:44px;border-radius:50%;cursor:pointer;
              background:rgba(255,255,255,.88);
              backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);
              border:1px solid rgba(0,0,0,.08);
              box-shadow:0 2px 10px rgba(0,0,0,.12);
              display:flex;align-items:center;justify-content:center;
              transition:all .2s ease;padding:0;color:#1f2937}
.theme-toggle svg{width:22px;height:22px;display:block}
.theme-toggle:hover{transform:scale(1.1);
                    box-shadow:0 4px 18px rgba(230,80,0,.3);
                    color:var(--naranja)}
.theme-toggle:active{transform:scale(.95)}
[data-theme="dark"] .theme-toggle{background:rgba(26,29,39,.85);
                                  border-color:rgba(255,255,255,.12);
                                  box-shadow:0 2px 10px rgba(0,0,0,.5);
                                  color:#ffd97a}
[data-theme="dark"] .theme-toggle:hover{box-shadow:0 4px 18px rgba(255,217,122,.35);
                                        color:#ffe69c}
@media(max-width:840px){
  .topbar-inner .descargar{margin-right:3.5rem}
}

[data-theme="dark"]{
  --bg:#0f1117;
  --card:#1a1d27;
  --borde:#2e3248;
  --texto:#e2e6f0;
  --texto-fuerte:#f5f7fa;
  --muted:#7a82a0;
  --naranja-soft:#3a2010;
  --crema:#1a1410;
}
[data-theme="dark"] body{background:var(--bg);color:var(--texto)}
[data-theme="dark"] .topbar{background:rgba(15,17,23,.92);
                            border-bottom-color:var(--borde)}
[data-theme="dark"] header h1{color:var(--texto-fuerte)}
[data-theme="dark"] .featured h2{color:var(--texto-fuerte)}
[data-theme="dark"] .featured .snippet,
[data-theme="dark"] .card .snippet{color:#a8b0c0}
[data-theme="dark"] .featured{box-shadow:0 8px 30px rgba(0,0,0,.4)}
[data-theme="dark"] .featured:hover{box-shadow:0 12px 40px rgba(255,122,42,.18)}
[data-theme="dark"] .card:hover{box-shadow:0 6px 20px rgba(255,122,42,.15)}
[data-theme="dark"] .toc{background:#22263a;border-color:var(--borde)}
[data-theme="dark"] .toc a{color:var(--texto)}
[data-theme="dark"] .sidebar{background:var(--card);border-color:var(--borde);
                             box-shadow:0 4px 12px rgba(0,0,0,.4)}
[data-theme="dark"] .contenido strong{color:var(--texto-fuerte)}
[data-theme="dark"] .contenido h2{border-bottom-color:#3a2818}
[data-theme="dark"] .contenido th{background:#2a1810;color:#ff9555}
[data-theme="dark"] .contenido a{color:#79b8ff}
[data-theme="dark"] footer{border-top-color:var(--borde);color:#6b7280}
[data-theme="dark"] .historico-titulo{color:#9ca3af}
[data-theme="dark"] .empty{background:var(--card);border-color:var(--borde)}
[data-theme="dark"] .card .meta,
[data-theme="dark"] .card{border-top-color:#2a2e44}
"""

SCROLLSPY_JS = """
<script>
(function(){
  var slugs = ['mercados','empresas','economia','internacional','innovacion','opinion'];
  var enlaces = document.querySelectorAll('.sidebar a');
  if(!enlaces.length) return;
  var secciones = [];
  slugs.forEach(function(s){
    var el = document.getElementById(s);
    if(el) secciones.push(el);
  });
  if(!secciones.length) return;
  var obs = new IntersectionObserver(function(entries){
    entries.forEach(function(e){
      if(e.isIntersecting){
        var id = e.target.id;
        enlaces.forEach(function(a){
          a.classList.toggle('active', a.getAttribute('href').endsWith('#'+id));
        });
      }
    });
  }, {rootMargin:'-25% 0px -60% 0px'});
  secciones.forEach(function(s){ obs.observe(s); });
})();
</script>
"""


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
html{scroll-behavior:smooth}
:root{
  --naranja:#E65000;--naranja-h:#ff6a1a;--naranja-soft:#fde6d6;
  --crema:#fff8f3;
  --bg:#fff;--card:#fff;--borde:#e5e7eb;
  --texto:#1f2937;--texto-fuerte:#111827;--muted:#6b7280;--link:#0056b3;
}
body{font-family:'Inter','Segoe UI',system-ui,-apple-system,sans-serif;
     background:var(--bg);color:var(--texto);line-height:1.7;margin:0;
     -webkit-font-smoothing:antialiased}
.topbar{position:sticky;top:0;background:rgba(255,255,255,.92);
        backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);
        border-bottom:1px solid var(--borde);padding:.75rem 1rem;z-index:10}
.topbar-inner{max-width:720px;margin:0 auto;display:flex;
              justify-content:space-between;align-items:center;gap:1rem}
.topbar a{text-decoration:none;font-weight:600;font-size:.9rem}
.topbar .volver{color:var(--naranja)}
.topbar .volver:hover{color:var(--naranja-h)}
.topbar .descargar{background:var(--naranja);color:#fff;padding:.45rem 1rem;
                   border-radius:8px;font-size:.85rem;transition:background .15s}
.topbar .descargar:hover{background:var(--naranja-h)}
.container{max-width:720px;margin:0 auto;padding:2.5rem 1.5rem 4rem}
header{margin-bottom:2.5rem}
header .etiqueta{display:inline-block;color:var(--naranja);font-size:.78rem;
                font-weight:700;text-transform:uppercase;letter-spacing:.1em;
                margin-bottom:.6rem}
header h1{font-size:1.7rem;color:var(--texto-fuerte);margin-bottom:.4rem;
          font-weight:800;letter-spacing:-.01em;line-height:1.25}
header .fecha{color:var(--muted);font-size:1rem}
.toc{background:var(--crema);border:1px solid var(--naranja-soft);
     border-radius:12px;padding:1.25rem 1.5rem;margin-bottom:2.5rem}
.toc-titulo{font-size:.78rem;font-weight:700;color:var(--naranja);
           text-transform:uppercase;letter-spacing:.1em;margin-bottom:.7rem}
.toc ul{list-style:none;margin:0;padding:0}
.toc li{margin:.05rem 0;font-size:.93rem;line-height:1.45}
.toc-l1>a{font-weight:600}
.toc-l2{padding-left:.9rem}
.toc-l3{padding-left:1.8rem;font-size:.86rem}
.toc-l3>a{color:var(--muted)}
.toc a{color:var(--texto);text-decoration:none;display:inline-block;
      padding:.18rem 0;transition:color .12s,transform .12s}
.toc a:hover{color:var(--naranja);transform:translateX(2px)}
.contenido{font-size:1.02rem}
.contenido h1,.contenido h2,.contenido h3{color:var(--naranja);
                                          margin:2rem 0 .8rem;font-weight:700;
                                          letter-spacing:-.005em;
                                          scroll-margin-top:80px}
.contenido h1{font-size:1.4rem}
.contenido h2{font-size:1.2rem;border-bottom:2px solid var(--naranja-soft);
              padding-bottom:.35rem}
.contenido h3{font-size:1.05rem}
.contenido p{margin-bottom:1rem}
.contenido ul,.contenido ol{margin:.5rem 0 1.2rem 1.5rem}
.contenido li{margin-bottom:.5rem}
.contenido li::marker{color:var(--naranja)}
.contenido strong{color:var(--texto-fuerte);font-weight:600}
.contenido a{color:var(--link)}
.contenido table{border-collapse:collapse;margin:1.2rem 0;width:100%;
                font-size:.95rem}
.contenido th,.contenido td{border:1px solid var(--borde);padding:.6rem .9rem;
                            text-align:left}
.contenido th{background:#fef3eb;color:var(--naranja);font-weight:600}
.contenido blockquote{border-left:3px solid var(--naranja);padding-left:1rem;
                     color:var(--muted);margin:1rem 0;font-style:italic}
footer{text-align:center;color:#9ca3af;font-size:.85rem;
       margin-top:4rem;padding-top:2rem;border-top:1px solid var(--borde)}
footer a{color:var(--naranja);text-decoration:none}
@media(max-width:640px){
  .container{padding:2rem 1rem 3rem}
  header h1{font-size:1.4rem}
  .topbar .descargar{padding:.4rem .8rem;font-size:.8rem}
}
"""


def convertir_docx_a_html_body(docx_path: str) -> str:
    """Convierte un .docx a HTML semántico (sin html/head/body wrappers)."""
    with open(docx_path, "rb") as f:
        result = mammoth.convert_to_html(f)
    return limpiar_instrucciones_word(result.value)


def limpiar_instrucciones_word(html: str) -> str:
    """Elimina párrafos de instrucciones de Word: textos entre corchetes
       o que mencionan atajos de teclado de Word (Ctrl+A, F9, etc.)."""
    soup = BeautifulSoup(html, "html.parser")
    for p in soup.find_all("p"):
        texto = p.get_text(strip=True)
        if not texto:
            continue
        # Párrafo entre corchetes (instrucción)
        if texto.startswith("[") and texto.endswith("]"):
            p.decompose()
            continue
        # Menciones explícitas de atajos de teclado de Word
        if re.search(r"\bCtrl\s*\+\s*[A-Z]", texto) and \
           re.search(r"\bF\d{1,2}\b", texto):
            p.decompose()
    return str(soup)


def _slugify(text: str, used_ids: set) -> str:
    """Convierte un título en un id válido para anchor (sin acentos, sin espacios)."""
    s = unicodedata.normalize("NFD", text)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-zA-Z0-9\s-]", "", s).strip().lower()
    s = re.sub(r"[\s-]+", "-", s) or "seccion"
    base, i = s, 1
    while s in used_ids:
        i += 1
        s = f"{base}-{i}"
    used_ids.add(s)
    return s


def construir_toc(html_body: str) -> tuple:
    """Inserta ids en los h1/h2/h3 del body y devuelve (html_modificado, toc_html)."""
    soup = BeautifulSoup(html_body, "html.parser")
    headings = soup.find_all(["h1", "h2", "h3"])

    used_ids = set()
    items = []
    for h in headings:
        texto = h.get_text(strip=True)
        if not texto:
            continue
        if not h.get("id"):
            h["id"] = _slugify(texto, used_ids)
        items.append({"level": int(h.name[1]), "text": texto, "id": h["id"]})

    if len(items) < 2:
        # No vale la pena un TOC con 0 o 1 entradas
        return str(soup), ""

    toc = ['<nav class="toc"><div class="toc-titulo">📍 En esta edición</div><ul>']
    for item in items:
        toc.append(
            f'<li class="toc-l{item["level"]}">'
            f'<a href="#{item["id"]}">{_escape_html(item["text"])}</a>'
            f'</li>'
        )
    toc.append("</ul></nav>")
    return str(soup), "".join(toc)


def extraer_snippet(html_body: str, max_len: int = 180) -> str:
    """Extrae las primeras palabras del primer párrafo significativo."""
    soup = BeautifulSoup(html_body, "html.parser")
    for p in soup.find_all("p"):
        texto = p.get_text(strip=True)
        if len(texto) > 30:
            if len(texto) > max_len:
                texto = texto[:max_len].rsplit(" ", 1)[0] + "…"
            return texto
    return ""


def _escape_html(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def renderizar_pagina_dia(fecha: datetime, html_body: str, docx_filename: str) -> str:
    """Envuelve el body convertido en una página HTML completa con TOC y sidebar."""
    fecha_humana = fecha_a_texto(fecha)
    dia_sem = DIAS_NOMBRE[fecha.weekday()]
    html_con_ids, toc_html = construir_toc(html_body)
    sidebar = render_sidebar()  # anchors internos (#mercados, #empresas, ...)

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{fecha_humana} · Resumen DF</title>
<style>{PAGINA_CSS}{SIDEBAR_CSS}{THEME_CSS}</style>
{THEME_INIT_JS}
</head>
<body>
{THEME_TOGGLE_HTML}
<nav class="topbar">
  <div class="topbar-inner">
    <a href="index.html" class="volver">← Todas las ediciones</a>
    <a href="{docx_filename}" download class="descargar">⬇ Word</a>
  </div>
</nav>
{sidebar}
<div class="container">
<header>
  <span class="etiqueta">Edición {dia_sem}</span>
  <h1>Resumen Diario Financiero</h1>
  <div class="fecha">{fecha_humana}</div>
</header>
{toc_html}
<div class="contenido">
{html_con_ids}
</div>
<footer>
  Análisis generado por Claude Cowork · Fuente: <a href="https://www.df.cl">df.cl</a>
</footer>
</div>
{SCROLLSPY_JS}
</body>
</html>
"""


# ─── ÍNDICE ───────────────────────────────────────────────────────────────────

INDEX_CSS = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --naranja:#E65000;--naranja-h:#ff6a1a;--naranja-soft:#fde6d6;
  --crema:#fff5ee;--bg:#fafafa;--card:#fff;--borde:#e5e7eb;
  --texto:#1f2937;--texto-fuerte:#111827;--muted:#6b7280;
}
body{font-family:'Inter','Segoe UI',system-ui,-apple-system,sans-serif;
     background:var(--bg);color:var(--texto);line-height:1.6;margin:0;
     min-height:100vh;-webkit-font-smoothing:antialiased}
.hero{background-image:
        linear-gradient(180deg,rgba(15,17,23,.55) 0%,rgba(15,17,23,.88) 100%),
        url('hero.jpg');
      background-size:cover;background-position:center 30%;
      color:#fff;text-align:center;padding:6rem 1.5rem 6.5rem;
      position:relative;overflow:hidden}
.hero::before{content:"";position:absolute;inset:0;
              background:radial-gradient(ellipse at 65% 25%,rgba(230,80,0,.22),transparent 55%);
              pointer-events:none}
.hero-content{position:relative;max-width:680px;margin:0 auto}
.hero h1{font-size:2.6rem;font-weight:800;letter-spacing:-.02em;
         margin-bottom:.7rem;line-height:1.15;
         text-shadow:0 2px 20px rgba(0,0,0,.5)}
.hero .tagline{font-size:1.1rem;opacity:.95;max-width:520px;margin:0 auto;
              line-height:1.5;text-shadow:0 2px 12px rgba(0,0,0,.6)}
.hero .badge{display:inline-block;background:rgba(255,255,255,.18);
            backdrop-filter:blur(8px);padding:.35rem 1rem;border-radius:30px;
            font-size:.78rem;font-weight:600;letter-spacing:.08em;
            text-transform:uppercase;margin-bottom:1.2rem}
.container{max-width:760px;margin:-2.5rem auto 0;padding:0 1.5rem 4rem;
           position:relative}
.featured{background:var(--card);border:1px solid var(--borde);
          border-radius:16px;padding:2rem 2.2rem;margin-bottom:2.5rem;
          text-decoration:none;color:inherit;display:block;
          transition:all .25s ease;box-shadow:0 8px 30px rgba(230,80,0,.1)}
.featured:hover{transform:translateY(-4px);
                box-shadow:0 12px 40px rgba(230,80,0,.18)}
.featured .label{display:inline-flex;align-items:center;gap:.4rem;
                background:var(--naranja);color:#fff;padding:.3rem .85rem;
                border-radius:30px;font-size:.72rem;font-weight:700;
                letter-spacing:.08em;text-transform:uppercase;
                margin-bottom:1.1rem}
.featured .label::before{content:"●";font-size:.6rem;
                        animation:pulse 2s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.featured h2{font-size:1.55rem;color:var(--texto-fuerte);margin-bottom:.35rem;
            font-weight:700;letter-spacing:-.01em}
.featured .fecha{color:var(--muted);font-size:.95rem;margin-bottom:1rem}
.featured .snippet{color:#4b5563;line-height:1.65;margin-bottom:1.2rem;
                  font-size:1rem}
.featured .cta{color:var(--naranja);font-weight:700;font-size:.95rem;
              display:inline-flex;align-items:center;gap:.3rem}
.featured:hover .cta{gap:.5rem}
.historico-titulo{font-size:.78rem;color:var(--muted);
                 text-transform:uppercase;letter-spacing:.12em;
                 font-weight:700;margin:2rem 0 1.2rem;padding-left:.2rem}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));
      gap:1rem}
.card{background:var(--card);border:1px solid var(--borde);
      border-radius:12px;padding:1.3rem 1.5rem;text-decoration:none;
      color:inherit;transition:all .2s ease;display:flex;
      flex-direction:column;gap:.6rem;position:relative}
.card:hover{border-color:var(--naranja);transform:translateY(-2px);
            box-shadow:0 6px 20px rgba(230,80,0,.1)}
.card .dia-semana{font-weight:700;color:var(--naranja);font-size:1rem;
                 letter-spacing:-.01em}
.card .fecha{color:var(--muted);font-size:.83rem;margin-top:-.3rem}
.card .snippet{color:#4b5563;font-size:.88rem;line-height:1.5;
              display:-webkit-box;-webkit-line-clamp:3;
              -webkit-box-orient:vertical;overflow:hidden;flex:1;min-height:3.9em}
.empty{text-align:center;color:var(--muted);padding:4rem 1.5rem;
       background:var(--card);border:1px dashed var(--borde);
       border-radius:12px}
footer{text-align:center;color:#9ca3af;font-size:.85rem;
       margin-top:4rem;padding-top:2.5rem;border-top:1px solid var(--borde)}
footer a{color:var(--naranja);text-decoration:none;font-weight:600}
footer a:hover{text-decoration:underline}
@media(max-width:600px){
  .hero{padding:3.5rem 1.2rem 4.5rem}
  .hero h1{font-size:2rem}
  .hero .tagline{font-size:1rem}
  .container{padding:0 1rem 3rem}
  .featured{padding:1.5rem 1.6rem}
  .featured h2{font-size:1.3rem}
  .grid{grid-template-columns:1fr}
}
"""


def generar_index(dias_publicados: list):
    """Construye docs/index.html con los días disponibles.
       dias_publicados es lista de (fecha, docx_filename, snippet)."""
    fecha_hoy_humana = fecha_a_texto(datetime.now())

    # Sidebar deep-linkea al resumen más reciente
    if dias_publicados:
        latest_fecha = dias_publicados[0][0].strftime("%Y-%m-%d")
        sidebar = render_sidebar(f"{latest_fecha}.html")
    else:
        sidebar = ""

    if not dias_publicados:
        cuerpo = '<p class="empty">Aún no hay resúmenes disponibles. Vuelve pronto.</p>'
    else:
        # Featured: el más reciente
        fecha_top, docx_top, snip_top = dias_publicados[0]
        fecha_iso_top = fecha_top.strftime("%Y-%m-%d")
        dia_sem_top = DIAS_NOMBRE[fecha_top.weekday()]
        snippet_top = _escape_html(snip_top) if snip_top else "Análisis del mercado del día."

        featured = f"""
    <a class="featured" href="{fecha_iso_top}.html">
      <span class="label">Última edición</span>
      <h2>{dia_sem_top}, {_escape_html(fecha_a_texto(fecha_top))}</h2>
      <p class="snippet">{snippet_top}</p>
      <span class="cta">Leer resumen completo →</span>
    </a>"""

        # Resto: en grid
        cards = []
        for fecha, docx_name, snippet in dias_publicados[1:]:
            fecha_iso = fecha.strftime("%Y-%m-%d")
            dia_sem = DIAS_NOMBRE[fecha.weekday()]
            snip_html = _escape_html(snippet) if snippet else "Resumen del día."
            cards.append(f"""
      <a class="card" href="{fecha_iso}.html">
        <div class="dia-semana">{dia_sem}</div>
        <div class="fecha">{_escape_html(fecha_a_texto(fecha))}</div>
        <div class="snippet">{snip_html}</div>
      </a>""")

        if cards:
            grid_html = f"""
    <div class="historico-titulo">Ediciones anteriores</div>
    <div class="grid">{''.join(cards)}</div>"""
        else:
            grid_html = ""

        cuerpo = featured + grid_html

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Resumen Diario Financiero · Análisis del mercado chileno</title>
<style>{INDEX_CSS}{SIDEBAR_CSS}{THEME_CSS}</style>
{THEME_INIT_JS}
</head>
<body>
{THEME_TOGGLE_HTML}
<section class="hero">
  <div class="hero-content">
    <span class="badge">📰 Análisis diario</span>
    <h1>Resumen Diario Financiero</h1>
    <p class="tagline">Noticias en minutos</p>
  </div>
</section>
{sidebar}
<main class="container">
  {cuerpo}

  <footer>
    Última actualización: {fecha_hoy_humana}<br>
    Fuente: <a href="https://www.df.cl">df.cl</a> · Análisis por Claude Cowork
  </footer>
</main>
</body>
</html>
"""

    with open(os.path.join(DOCS_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)


# ─── LIMPIEZA ─────────────────────────────────────────────────────────────────

def limpiar_docs(fechas_validas: set):
    """Borra de docs/:
       - YYYY-MM-DD.{html,docx} cuya fecha no esté en fechas_validas.
       - Cualquier YYYY-MM-DD-noticias.{html,docx} (feature retirada)."""
    if not os.path.exists(DOCS_DIR):
        return
    patron_resumen = re.compile(r"^(\d{4}-\d{2}-\d{2})\.(html|docx)$")
    patron_noticias = re.compile(r"^\d{4}-\d{2}-\d{2}-noticias\.(html|docx)$")
    for archivo in os.listdir(DOCS_DIR):
        eliminar = False
        m = patron_resumen.match(archivo)
        if m and m.group(1) not in fechas_validas:
            eliminar = True
        elif patron_noticias.match(archivo):
            eliminar = True
        if eliminar:
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
            snippet = extraer_snippet(html_body)
            pagina = renderizar_pagina_dia(fecha, html_body, docx_dest)
        except Exception as e:
            print(f"     ❌ Error convirtiendo resumen: {e}")
            continue

        with open(os.path.join(DOCS_DIR, html_dest), "w", encoding="utf-8") as f:
            f.write(pagina)
        shutil.copy2(docx_path, os.path.join(DOCS_DIR, docx_dest))
        publicados.append((fecha, docx_dest, snippet))

    fechas_validas = {f.strftime("%Y-%m-%d") for f, _, _ in publicados}
    limpiar_docs(fechas_validas)
    generar_index(publicados)

    print(f"\n🌐 Sitio generado: {os.path.join(DOCS_DIR, 'index.html')}")
    print("\n🚀 Pusheando a GitHub...")
    push_a_github()


if __name__ == "__main__":
    main()
