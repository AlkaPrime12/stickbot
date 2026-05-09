import easyocr
import cv2
import difflib
import math
import sqlite3
import os
import numpy as np

print("Cargando modelo de IA en memoria...")
lector = easyocr.Reader(["en"])
DIRECTORIO_BASE = os.path.dirname(os.path.abspath(__file__))
RUTA_DB = os.path.join(DIRECTORIO_BASE, "stickbot.db")


def obtener_color_texto(imagen_recorte, caja_coordenadas):
    x_min = int(min(p[0] for p in caja_coordenadas))
    x_max = int(max(p[0] for p in caja_coordenadas))
    y_min = int(min(p[1] for p in caja_coordenadas))
    y_max = int(max(p[1] for p in caja_coordenadas))

    micro_recorte = imagen_recorte[max(0, y_min):y_max, max(0, x_min):x_max]
    gris = cv2.cvtColor(micro_recorte, cv2.COLOR_BGR2GRAY)
    _, mascara = cv2.threshold(gris, 100, 255, cv2.THRESH_BINARY)

    color_bgr = cv2.mean(micro_recorte, mask=mascara)[:3]
    return color_bgr


def _resolve_db_path(db_path: str | None) -> str:
    if db_path:
        return db_path
    try:
        from app.config import settings

        return settings.database_path
    except Exception:
        return RUTA_DB


def analizar_captura(imagen_bytes, db_path=None, ocr_options=None):
    """
    OCR de captura de partida. ocr_options puede incluir:
    ocr_margin_percent, ocr_corner_confidence, ocr_center_confidence,
    ocr_color_distance_max, ocr_confidence_threshold (legacy / umbral extra en centro).
    """
    opts = ocr_options or {}
    margin_pct = float(opts.get("ocr_margin_percent", 20.0)) / 100.0
    corner_conf = float(opts.get("ocr_corner_confidence", 0.10))
    center_conf_base = float(opts.get("ocr_center_confidence", 0.25))
    legacy_center = float(opts.get("ocr_confidence_threshold", 0.25))
    center_conf = max(center_conf_base, legacy_center)
    umbral_tol = float(opts.get("ocr_color_distance_max", 170.0))

    db_file = _resolve_db_path(db_path)

    nparr = np.frombuffer(imagen_bytes, np.uint8)
    imagen_original = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if imagen_original is None:
        raise ValueError("No se pudo decodificar la imagen adjunta.")

    alto, ancho, _ = imagen_original.shape

    margen_y = int(alto * margin_pct)
    margen_x = int(ancho * margin_pct)

    esquinas = {
        "Arriba_Izquierda": imagen_original[0:margen_y, 0:margen_x],
        "Arriba_Derecha": imagen_original[0:margen_y, ancho - margen_x : ancho],
        "Abajo_Izquierda": imagen_original[alto - margen_y : alto, 0:margen_x],
        "Abajo_Derecha": imagen_original[alto - margen_y : alto, ancho - margen_x : ancho],
    }

    datos_puntajes = []
    for recorte in esquinas.values():
        zoom = cv2.resize(recorte, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        resultados = lector.readtext(zoom)
        for caja, texto, confianza in resultados:
            if confianza > corner_conf and texto.isdigit() and len(texto) <= 2:
                color = obtener_color_texto(zoom, caja)
                datos_puntajes.append({"puntos": int(texto), "color": color})

    conexion = sqlite3.connect(db_file)
    cursor = conexion.cursor()
    cursor.execute("SELECT nombre_juego FROM jugadores")
    jugadores_bd = [fila[0] for fila in cursor.fetchall()]
    conexion.close()

    centro = imagen_original[margen_y : alto - margen_y, 0:ancho]
    resultados_centro = lector.readtext(centro)

    datos_jugadores = []
    for caja, texto, confianza in resultados_centro:
        if confianza > center_conf:
            nombre_limpio = ""
            if ":" in texto:
                nombre_limpio = texto.split(":")[0].strip()
            elif len(texto) > 3 and "ms" not in texto.lower() and texto.lower() not in ["landiall", "landfall"]:
                if not texto.isdigit():
                    nombre_limpio = texto.strip()

            if nombre_limpio:
                coincidencias = difflib.get_close_matches(nombre_limpio, jugadores_bd, n=1, cutoff=0.5)
                nombre_final = coincidencias[0] if coincidencias else nombre_limpio
                color = obtener_color_texto(centro, caja)
                datos_jugadores.append({"nombre": nombre_final, "color": color})

    resultados_finales = {}

    for jugador in datos_jugadores:
        color_jugador = jugador["color"]
        puntaje_mas_cercano = 0
        distancia_minima = float("inf")

        for puntaje in datos_puntajes:
            color_puntaje = puntaje["color"]
            distancia = math.dist(color_jugador, color_puntaje)
            if distancia < distancia_minima:
                distancia_minima = distancia
                puntaje_mas_cercano = puntaje["puntos"]

        if distancia_minima <= umbral_tol:
            resultados_finales[jugador["nombre"]] = puntaje_mas_cercano
        else:
            print(
                f"Descartando texto: '{jugador['nombre']}' (Distancia de color: {round(distancia_minima)} > {umbral_tol})"
            )

    return resultados_finales
