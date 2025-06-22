import streamlit as st
import gpxpy
import math
import os
import matplotlib.pyplot as plt
from PIL import Image
from pathlib import Path
import base64
from urllib.parse import urlencode

from strava_utils import (
    get_segments_from_activity,
    intercambiar_codigo_por_token,
    sesion_iniciada,
    cerrar_sesion_strava,
    obtener_datos_atleta,
    get_streams_for_activity
)

# === CONFIGURACIÓN BÁSICA ===
st.set_page_config(page_title="Calculadora Rompe KOM's 🚴‍♂️", layout="centered")

# === LOGO ===
def cargar_logo(path):
    with open(path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

light_logo = cargar_logo("logo_light.png")
dark_logo = cargar_logo("logo_dark.png")

# === CABECERA ===
st.markdown("<br>", unsafe_allow_html=True)
col1, col2 = st.columns([6, 1])
with col1:
    st.markdown("## 🔥 CALCULADORA ROMPE KOM'S")
    st.caption("Analiza el esfuerzo necesario para tus segmentos favoritos de ciclismo usando tu FTP, peso y equipo.")
with col2:
    logo_html = f"""
    <picture>
        <source media="(prefers-color-scheme: dark)" srcset="data:image/png;base64,{light_logo}">
        <source media="(prefers-color-scheme: light)" srcset="data:image/png;base64,{dark_logo}">
        <img src="data:image/png;base64,{light_logo}" style="max-width: 100px; margin-top: 0.8rem;" alt="Logo">
    </picture>
    """
    st.markdown(logo_html, unsafe_allow_html=True)

# === AUTENTICACIÓN STRAVA ===
if "token_guardado" not in st.session_state:
    st.session_state["token_guardado"] = False

query_params = st.query_params
if "code" in query_params and not st.session_state["token_guardado"]:
    code = query_params["code"]
    token_info = intercambiar_codigo_por_token(code)
    if token_info:
        st.session_state["token_guardado"] = True
        st.success("✅ Autenticación completada. Puedes continuar.")
        st.rerun()
    else:
        st.error("❌ Fallo al obtener token. Intenta iniciar sesión nuevamente.")
        st.stop()

# === MENÚ LATERAL STRAVA ===
if sesion_iniciada():
    datos = obtener_datos_atleta()
    if datos:
        col1, col2 = st.sidebar.columns([1, 3])
        col1.image(datos["profile"], width=50)
        col2.markdown(f"**{datos['firstname']} {datos['lastname']}**")

        if st.sidebar.button("🔓 Cerrar sesión"):
            cerrar_sesion_strava()
            st.rerun()
else:
    auth_url = (
        f"https://www.strava.com/oauth/authorize?client_id=141324"
        f"&redirect_uri=https://rompekoms.streamlit.app/"
        f"&response_type=code&scope=activity:read_all"
    )
    st.sidebar.link_button("🔐 Iniciar sesión con Strava", auth_url)

# === INTERFAZ PRINCIPAL ===
modo = st.radio("Selecciona el modo de entrada:", ["📂 Archivo GPX", "🌐 Actividad de Strava"], horizontal=True)
gpx_file = None
actividad_id = ""

if modo == "📂 Archivo GPX":
    gpx_file = st.file_uploader("📂 Sube tu archivo GPX", type=["gpx"])
elif modo == "🌐 Actividad de Strava":
    actividad_input = st.text_input("🔗 Pega el link o ID de una actividad pública de Strava", placeholder="Ej. https://www.strava.com/activities/123456789")
    if "activities" in actividad_input:
        actividad_id = actividad_input.strip().split("activities/")[-1].split("/")[0]
    else:
        actividad_id = actividad_input.strip()

peso_ciclista = st.number_input("🏋️ Peso del ciclista (kg)", value=62.0)
peso_bici = st.number_input("🚲 Peso bici + equipo (kg)", value=8.0)
tipo_bici = st.selectbox("Tipo de bicicleta", options=[
    "🚴‍♂️ Ruta", "🚰 Triatlón/Cabrita", "🚵‍♀️ MTB", "🚲 Urbana"
])
ftp = st.number_input("⚡ Tu FTP (watts)", value=275)
tiempo_objetivo = st.text_input("🍏 Tiempo objetivo (opcional, formato mm o mm:ss)", value="")

bicis = {
    "🚴‍♂️ Ruta": {"CdA": 0.32, "Crr": 0.004},
    "🚰 Triatlón/Cabrita": {"CdA": 0.25, "Crr": 0.0035},
    "🚵‍♀️ MTB": {"CdA": 0.4, "Crr": 0.008},
    "🚲 Urbana": {"CdA": 0.38, "Crr": 0.006},
}
CdA = bicis[tipo_bici]["CdA"]
Crr = bicis[tipo_bici]["Crr"]
rho = 1.225
g = 9.81

# === FUNCIONES ===
def estimar_potencia(distancia, elevacion, tiempo_s, masa_total):
    pendiente_media = elevacion / distancia if distancia != 0 else 0
    velocidad = distancia / tiempo_s
    P_gravedad = masa_total * g * pendiente_media * velocidad
    P_rodadura = masa_total * g * Crr * velocidad
    P_aire = 0.5 * rho * CdA * velocidad**3
    return P_gravedad + P_rodadura + P_aire

def graficar_elevacion(distancias_km, elevaciones):
    plt.figure(figsize=(8, 3))
    plt.plot(distancias_km, elevaciones)
    plt.xlabel("Distancia (km)")
    plt.ylabel("Altura (m)")
    plt.title("Perfil del Segmento")
    st.pyplot(plt)

def mostrar_leyenda():
    with st.expander("📘 Leyenda de colores (dificultad por pendiente promedio)"):
        st.markdown("""
        - 🟪 **Subida muy fuerte** (> 8%)
        - 🟥 **Subida fuerte** (6% - 8%)
        - 🟧 **Subida media** (4% - 6%)
        - 🟨 **Ligera subida** (2% - 4%)
        - 🟩 **Plano** (< 2%)
        """)

def procesar_segmento(total_dist, total_elev, masa_total):
    total_dist_km = total_dist / 1000
    st.markdown(f"📏 **Distancia:** {total_dist_km:.2f} km")
    st.markdown(f"👩‍🏋 **Desnivel:** {total_elev:.0f} m")

    if tiempo_objetivo:
        try:
            partes = tiempo_objetivo.strip().split(":")
            minutos = int(partes[0])
            segundos = int(partes[1]) if len(partes) > 1 else 0
            tiempo_s = minutos * 60 + segundos
            potencia_necesaria = estimar_potencia(total_dist, total_elev, tiempo_s, masa_total)
            vatio_kilo = potencia_necesaria / peso_ciclista
            peso_objetivo = ftp / vatio_kilo

            st.markdown("---")
            st.subheader("📊 Resultado estimado")
            st.success(f"⚡ Para hacerlo en {minutos}:{segundos:02d} min, necesitas aprox. **{potencia_necesaria:.0f}w**")
            st.info(f"📈 Eso equivale a **{vatio_kilo:.2f} w/kg**")
            st.warning(f"⚖️ Para lograrlo con tu FTP actual (**{ftp:.0f}w**), tu peso debería ser **{peso_objetivo:.1f} kg**")
            st.caption(f"💡 O mantener tu peso actual (**{peso_ciclista:.1f}kg**) y subir tu FTP a **{potencia_necesaria:.0f}w**.")

        except:
            st.error("⚠️ El formato del tiempo es incorrecto. Usa `mm` o `mm:ss`")
    else:
        potencia = ftp * 0.9
        pendiente_media = total_elev / total_dist if total_dist != 0 else 0

        def encontrar_velocidad(p):
            v = 1.0
            for _ in range(1000):
                Pg = masa_total * g * pendiente_media * v
                Pr = masa_total * g * Crr * v
                Pa = 0.5 * rho * CdA * v**3
                P_total = Pg + Pr + Pa
                error = p - P_total
                if abs(error) < 0.1:
                    return v
                v += error / 200
            return v

        velocidad = encontrar_velocidad(potencia)
        tiempo_seg = total_dist / velocidad
        tiempo_min = tiempo_seg / 60

        st.markdown("---")
        st.subheader("📊 Resultado estimado")
        st.success(f"⏱️ Con **{potencia:.0f}w**, completarías el segmento en **{tiempo_min:.1f} minutos**")
        st.caption("📌 Asumiendo que puedes sostener el 90% de tu FTP.")

# === PROCESO PARA SEGMENTO STRAVA ===
if actividad_id:
    segmentos = get_segments_from_activity(actividad_id)
    if not segmentos:
        st.error("❌ No se encontraron segmentos o hubo un error con la API.")
    else:
        masa_total = peso_ciclista + peso_bici
        segmentos = sorted(segmentos, key=lambda s: -estimar_potencia(
            s['segment']['distance'],
            s['segment']['elevation_high'] - s['segment']['elevation_low'],
            (s['segment']['distance'] / (ftp * 0.9)),
            masa_total
        ))

        st.success(f"✅ {len(segmentos)} segmentos encontrados.")
        mostrar_leyenda()

        opciones_coloreadas = []
        for s in segmentos:
            nombre = s['segment']['name']
            distancia = s['segment']['distance']
            elev = s['segment']['elevation_high'] - s['segment']['elevation_low']
            grad = elev / distancia if distancia != 0 else 0
            color = "🟪" if grad > 0.08 else "🟥" if grad > 0.06 else "🟧" if grad > 0.04 else "🟨" if grad > 0.02 else "🟩"
            opciones_coloreadas.append(f"{color} {nombre} ({distancia/1000:.2f} km)")

        selected = st.selectbox("Elige un segmento para analizar:", opciones_coloreadas)
        seleccionado = segmentos[opciones_coloreadas.index(selected)]

        if seleccionado:
            distancia = seleccionado['segment']['distance']
            elevacion = seleccionado['segment']['elevation_high'] - seleccionado['segment']['elevation_low']
            masa_total = peso_ciclista + peso_bici
            procesar_segmento(distancia, elevacion, masa_total)

            st.subheader("📈 Perfil del Segmento")
            stream = None
            try:
                stream = get_streams_for_activity(actividad_id)
            except:
                pass

            if stream and 'altitude' in stream and 'distance' in stream:
                dist_data = stream['distance']['data']
                alt_data = stream['altitude']['data']
                start = seleccionado.get('start_index', 0)
                end = seleccionado.get('end_index', len(dist_data))

                if 0 <= start < end <= len(dist_data):
                    segmento_dist = dist_data[start:end]
                    segmento_alt = alt_data[start:end]
                    distancias = [d / 1000 for d in segmento_dist]
                    graficar_elevacion(distancias, segmento_alt)
                else:
                    st.warning("⚠️ No se pudo recortar el segmento correctamente.")
            else:
                st.warning("⚠️ No se pudo obtener el perfil de elevación.")

# === GPX ===
if gpx_file:
    gpx = gpxpy.parse(gpx_file)

    distancias = []
    elevaciones = []
    total_dist = 0.0
    last_point = None

    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                if last_point:
                    d = point.distance_3d(last_point)
                    if d is not None:
                        total_dist += d
                distancias.append(total_dist / 1000)
                elevaciones.append(point.elevation)
                last_point = point

    if len(distancias) > 1 and len(elevaciones) > 1:
        masa_total = peso_ciclista + peso_bici
        total_elev = max(elevaciones) - min(elevaciones)
        procesar_segmento(total_dist, total_elev, masa_total)
        st.subheader("📈 Perfil del Segmento")
        graficar_elevacion(distancias, elevaciones)
    else:
        st.warning("⚠️ El archivo GPX no tiene datos suficientes.")

# === PIE DE PÁGINA ===
st.markdown("""
---
<p style='text-align: center; font-size: 0.8rem;'>🛠️ Desarrollado con cariño por <b>Yobwear</b> — v1.0</p>
""", unsafe_allow_html=True)
