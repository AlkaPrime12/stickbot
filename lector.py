import easyocr
import cv2
import difflib
import math
import sqlite3
import os
import numpy as np # Nueva librería para manejar la RAM

# Inicializamos el lector fuera de la función
print("Cargando modelo de IA en memoria...")
lector = easyocr.Reader(['en'])
DIRECTORIO_BASE = os.path.dirname(os.path.abspath(__file__))
RUTA_DB = os.path.join(DIRECTORIO_BASE, 'stickbot.db')

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

def analizar_captura(imagen_bytes): # Ahora recibe bytes, no una ruta
    # Convertimos los bytes de la RAM en una imagen que OpenCV entienda
    nparr = np.frombuffer(imagen_bytes, np.uint8)
    imagen_original = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    alto, ancho, _ = imagen_original.shape

    margen_y = int(alto * 0.20)
    margen_x = int(ancho * 0.20)

    esquinas = {
        "Arriba_Izquierda": imagen_original[0:margen_y, 0:margen_x],
        "Arriba_Derecha": imagen_original[0:margen_y, ancho-margen_x:ancho],
        "Abajo_Izquierda": imagen_original[alto-margen_y:alto, 0:margen_x],
        "Abajo_Derecha": imagen_original[alto-margen_y:alto, ancho-margen_x:ancho]
    }

    # --- FASE 1: PUNTAJES ---
    datos_puntajes = []
    for posicion, recorte in esquinas.items():
        zoom = cv2.resize(recorte, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        resultados = lector.readtext(zoom)
        for caja, texto, confianza in resultados:
            if confianza > 0.1 and texto.isdigit() and len(texto) <= 2:
                color = obtener_color_texto(zoom, caja)
                datos_puntajes.append({'puntos': int(texto), 'color': color})

    # --- FASE 2: NOMBRES ---
    conexion = sqlite3.connect(RUTA_DB)
    cursor = conexion.cursor()
    cursor.execute('SELECT nombre_juego FROM jugadores')
    jugadores_bd = [fila[0] for fila in cursor.fetchall()]
    conexion.close()

    centro = imagen_original[margen_y : alto-margen_y, 0 : ancho]
    resultados_centro = lector.readtext(centro)
    
    datos_jugadores = []
    for caja, texto, confianza in resultados_centro:
        if confianza > 0.25:
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
                datos_jugadores.append({'nombre': nombre_final, 'color': color})

# --- FASE 3: EMPAREJAMIENTO Y FILTRADO DE COLOR ---
    resultados_finales = {}
    
    # La distancia máxima permitida entre dos colores para considerarlos "el mismo"
    # (0 es idéntico, 441 es el opuesto exacto entre blanco y negro)
    UMBRAL_TOLERANCIA = 170 

    for jugador in datos_jugadores:
        color_jugador = jugador['color']
        puntaje_mas_cercano = 0
        distancia_minima = float('inf')
        
        for puntaje in datos_puntajes:
            color_puntaje = puntaje['color']
            distancia = math.dist(color_jugador, color_puntaje)
            if distancia < distancia_minima:
                distancia_minima = distancia
                puntaje_mas_cercano = puntaje['puntos']
                
        # EL GUARDIA DE COLOR: 
        # Si la distancia mínima es menor al umbral, lo consideramos un jugador válido.
        # Si es mayor (ej. texto blanco vs jugador rojo), se descarta completamente.
        if distancia_minima <= UMBRAL_TOLERANCIA:
            resultados_finales[jugador['nombre']] = puntaje_mas_cercano
        else:
            # (Opcional) Imprimimos en la terminal qué ignoró para que puedas debugear
            print(f"🗑️ Descartando texto: '{jugador['nombre']}' (Distancia de color: {round(distancia_minima)} > {UMBRAL_TOLERANCIA})")

    return resultados_finales