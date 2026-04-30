#!/usr/bin/env python3
"""
Interfaz web para el Scraper Diario Financiero.
Ejecutar: python app.py  → abre http://localhost:5000 automáticamente
"""

from flask import Flask, render_template, Response, jsonify, stream_with_context
import threading
import queue
import sys
import os
import json
from datetime import datetime, timedelta

app = Flask(__name__)

_log_queue = queue.Queue()
_running = False
_lock = threading.Lock()


class QueueWriter:
    """Captura print() y lo manda al queue para SSE."""
    def __init__(self, q, original):
        self.q = q
        self.original = original

    def write(self, text):
        self.original.write(text)
        self.original.flush()
        if text.strip():
            self.q.put(text.rstrip())

    def flush(self):
        self.original.flush()


def run_scraper(modo):
    global _running
    with _lock:
        if _running:
            return
        _running = True

    old_stdout = sys.stdout
    sys.stdout = QueueWriter(_log_queue, old_stdout)

    try:
        from scraper_df import scrapear_dia, detectar_dias_faltantes
        import time
        hoy = datetime.now()

        if modo == "dia":
            scrapear_dia(hoy)

        elif modo == "semana":
            print("Modo semana: últimos 7 días hábiles")
            dias_habiles = [
                hoy - timedelta(days=i)
                for i in range(6, -1, -1)
                if (hoy - timedelta(days=i)).weekday() < 5
            ]
            for i, fecha in enumerate(dias_habiles):
                scrapear_dia(fecha)
                if i < len(dias_habiles) - 1:
                    time.sleep(3)

        elif modo == "recuperar":
            faltantes = detectar_dias_faltantes()
            if faltantes:
                print(f"Recuperando {len(faltantes)} días perdidos...")
                for fecha in faltantes:
                    scrapear_dia(fecha)
                    time.sleep(3)
            else:
                print("No hay días pendientes.")

    except Exception as e:
        _log_queue.put(f"Error: {e}")
    finally:
        sys.stdout = old_stdout
        _running = False
        _log_queue.put("__DONE__")


# ─── RUTAS ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/run/<modo>")
def run(modo):
    if modo not in ("dia", "semana", "recuperar"):
        return jsonify({"error": "modo inválido"}), 400
    if _running:
        return jsonify({"error": "Ya hay un proceso en curso"}), 409
    t = threading.Thread(target=run_scraper, args=(modo,), daemon=True)
    t.start()
    return jsonify({"ok": True})


@app.route("/stream")
def stream():
    def generate():
        while True:
            try:
                msg = _log_queue.get(timeout=60)
                if msg == "__DONE__":
                    yield f"data: {json.dumps({'done': True})}\n\n"
                    break
                yield f"data: {json.dumps({'log': msg})}\n\n"
            except queue.Empty:
                yield 'data: {"heartbeat": true}\n\n'
    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.route("/estado")
def estado():
    return jsonify({"running": _running})


@app.route("/archivos")
def archivos():
    from scraper_df import CARPETA_SALIDA
    resultado = []
    if os.path.exists(CARPETA_SALIDA):
        for nombre in sorted(os.listdir(CARPETA_SALIDA), reverse=True)[:20]:
            ruta_carpeta = os.path.join(CARPETA_SALIDA, nombre)
            if os.path.isdir(ruta_carpeta):
                archivos_dia = sorted(os.listdir(ruta_carpeta))
                resultado.append({"fecha": nombre, "archivos": archivos_dia})
    return jsonify(resultado)


@app.route("/abrir-carpeta/<fecha>")
def abrir_carpeta(fecha):
    from scraper_df import CARPETA_SALIDA
    ruta = os.path.join(CARPETA_SALIDA, fecha)
    if os.path.exists(ruta):
        os.startfile(ruta)
        return jsonify({"ok": True})
    return jsonify({"error": "No encontrado"}), 404


@app.route("/abrir-archivo/<fecha>/<nombre>")
def abrir_archivo(fecha, nombre):
    from scraper_df import CARPETA_SALIDA
    ruta = os.path.join(CARPETA_SALIDA, fecha, nombre)
    if os.path.exists(ruta):
        os.startfile(ruta)
        return jsonify({"ok": True})
    return jsonify({"error": "No encontrado"}), 404


# ─── INICIO ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import webbrowser
    webbrowser.open("http://localhost:5000")
    app.run(debug=False, threaded=True, port=5000)
