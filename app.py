import streamlit as st
import gpxpy
import math
import os
import matplotlib.pyplot as plt
from urllib.parse import urlparse, parse_qs

from strava_utils import (
    get_segments_from_activity,
    sesion_iniciada,
    cerrar_sesion_strava,
    obtener_datos_atleta,
    get_streams_for_activity,
    intercambiar_codigo_por_token
)

# === CONFIGURACIÓN GENERAL ===
st.set_page_config(page_title="Calculadora de Segmentos 🚴‍♂️", layout="centered")

# === AUTENTICACIÓN STRAVA ===
query_params = st.query_params
code = query_params.get("code")
if code:
    token_data = intercambiar_codigo_por_token(code)
    if token_data:
        st.success("✅ ¡Sesión iniciada correctamente!")
        st.query_params.clear()
        st.rerun()
    else:
        st.error("❌ Error al obtener token de Strava.")

# === CABECERA ===
tema = st.get_option("theme.base")
logo_path = "logo_dark.png" if tema == "dark" else "logo_light.png"
col1, col2 = st.columns([4, 1])
with col1:
    st.markdown("## 🔥 CALCULADORA ROMPE KOM'S")
    st.markdown("Analiza tus segmentos favoritos usando tu FTP, peso y tipo de bici.")
with col2:
    if os.path.exists(logo_path):
        st.image(logo_path, width=100)

# === MODO DE ENTRADA ===
modo = st.radio("Selecciona el modo de entrada:", ["📂 Archivo GPX", "🌐 Segmento Strava"], horizontal=True)

# === AUTENTICACIÓN STRAVA (solo si eligen modo STRAVA) ===
actividad_id = None
if modo == "🌐 Segmento Strava":
    if not sesion_iniciada():
        client_id = "141324"
        redirect_uri = "https://rompekoms.streamlit.app/"
        scope = "read,activity:read_all"
        auth_url = f"https://www.strava.com/oauth/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&approval_prompt=auto&scope={scope}"
        st.markdown(f"[🔐 Iniciar sesión con Strava]({auth_url})", unsafe_allow_html=True)
    else:
        datos = obtener_datos_atleta()
        if datos:
            col1, col2 = st.columns([1, 6])
            col1.image(datos["profile"], width=50)
            col2.markdown(f"**{datos['firstname']} {datos['lastname']}**")
            if st.button("🔓 Cerrar sesión"):
                cerrar_sesion_strava()
                st.rerun()

# === ARCHIVO GPX O LINK STRAVA ===
gpx_file = None
if modo == "📂 Archivo GPX":
    gpx_file = st.file_uploader("📁 Sube tu archivo GPX", type=["gpx"])
elif modo == "🌐 Segmento Strava":
    actividad_url = st.text_input("🔗 Pega el link o ID de una actividad pública de Strava")
    if actividad_url:
        try:
            if "activities" in actividad_url:
                actividad_id = actividad_url.split("/")[-1]
            else:
                actividad_id = actividad_url
        except:
            st.error("❌ Link inválido")

# === DATOS DEL USUARIO ===
col1, col2 = st.columns(2)
peso_ciclista = col1.number_input("🏋️ Peso del ciclista (kg)", value=62.0)
peso_bici = col2.number_input("🚲 Peso bici + equipo (kg)", value=8.0)
altura = st.number_input("📏 Altura (cm)", value=170)
tipo_bici = st.selectbox("Tipo de bicicleta", options=["🚴‍♂️ Ruta", "🛞 Triatlón/Cabrita", "🚵‍♀️ MTB", "🚲 Urbana"])
ftp = st.number_input("⚡ Tu FTP (watts)", value=275)
tiempo_objetivo = st.text_input("🎯 Tiempo objetivo (opcional, formato mm o mm:ss)", value="")

# === PARÁMETROS ===
bicis = {
    "🚴‍♂️ Ruta": {"CdA": 0.32, "Crr": 0.004},
    "🛞 Triatlón/Cabrita": {"CdA": 0.25, "Crr": 0.0035},
    "🚵‍♀️ MTB": {"CdA": 0.4, "Crr": 0.008},
    "🚲 Urbana": {"CdA": 0.38, "Crr": 0.006},
}
CdA = bicis[tipo_bici]["CdA"]
Crr = bicis[tipo_bici]["Crr"]
rho = 1.225
g = 9.81

# === FUNCIONES ===
def estimar_potencia(dist, elev, tiempo_s, masa):
    pendiente = elev / dist if dist != 0 else 0
    v = dist / tiempo_s
    return masa * g * pendiente * v + masa * g * Crr * v + 0.5 * rho * CdA * v**3

def graficar(distancias, elevaciones):
    plt.figure(figsize=(8, 3))
    plt.plot(distancias, elevaciones)
    plt.xlabel("Distancia (km)")
    plt.ylabel("Altura (m)")
    plt.title("Perfil del Segmento")
    st.pyplot(plt)

def procesar(dist, elev, masa):
    dist_km = dist / 1000
    st.markdown(f"📏 **Distancia:** {dist_km:.2f} km")
    st.markdown(f"🧗 **Desnivel:** {elev:.0f} m")
    if tiempo_objetivo:
        try:
            partes = tiempo_objetivo.strip().split(":")
            minutos = int(partes[0])
            segundos = int(partes[1]) if len(partes) > 1 else 0
            tiempo_s = minutos * 60 + segundos
            potencia = estimar_potencia(dist, elev, tiempo_s, masa)
            wkg = potencia / peso_ciclista
            peso_obj = ftp / wkg
            st.markdown("---")
            st.subheader("📊 Resultado estimado")
            st.success(f"⚡ Necesitas aprox. **{potencia:.0f}w**")
            st.info(f"📈 Eso equivale a **{wkg:.2f} w/kg**")
            st.warning(f"⚖️ Peso necesario con tu FTP: **{peso_obj:.1f} kg**")
        except:
            st.error("⚠️ Tiempo mal escrito. Usa mm o mm:ss")
    else:
        potencia = ftp * 0.9
        pendiente = elev / dist if dist != 0 else 0
        def buscar_velocidad(p):
            v = 1.0
            for _ in range(1000):
                total = masa * g * pendiente * v + masa * g * Crr * v + 0.5 * rho * CdA * v**3
                error = p - total
                if abs(error) < 0.1:
                    return v
                v += error / 200
            return v
        v = buscar_velocidad(potencia)
        tiempo_min = (dist / v) / 60
        st.markdown("---")
        st.subheader("📊 Resultado estimado")
        st.success(f"⏱️ Con **{potencia:.0f}w**, tardarías aprox. **{tiempo_min:.1f} minutos**")

# === PROCESAMIENTO DE GPX ===
if gpx_file:
    gpx = gpxpy.parse(gpx_file.read().decode("utf-8"))
    total_dist = 0
    total_elev = 0
    puntos = []
    for track in gpx.tracks:
        for seg in track.segments:
            puntos.extend(seg.points)
            for i in range(1, len(seg.points)):
                d = seg.points[i-1].distance_3d(seg.points[i])
                elev = max(0, seg.points[i].elevation - seg.points[i-1].elevation)
                total_dist += d
                total_elev += elev
    distancias = []
    elevaciones = []
    dist_acumulada = 0
    for i in range(1, len(puntos)):
        d = puntos[i-1].distance_3d(puntos[i])
        dist_acumulada += d
        distancias.append(dist_acumulada / 1000)
        elevaciones.append(puntos[i].elevation)
    masa_total = peso_ciclista + peso_bici
    graficar(distancias, elevaciones)
    procesar(total_dist, total_elev, masa_total)

# === PROCESAMIENTO DE STRAVA ===
elif actividad_id:
    segmentos = get_segments_from_activity(actividad_id)
    if not segmentos:
        st.error("❌ No se encontraron segmentos.")
    else:
        masa_total = peso_ciclista + peso_bici
        segmentos = sorted(segmentos, key=lambda s: -estimar_potencia(
            s['segment']['distance'],
            s['segment']['elevation_high'] - s['segment']['elevation_low'],
            (s['segment']['distance'] / (ftp * 0.9)),
            masa_total
        ))
        st.success(f"✅ {len(segmentos)} segmentos encontrados.")
        opciones = []
        for s in segmentos:
            dist = s['segment']['distance']
            elev = s['segment']['elevation_high'] - s['segment']['elevation_low']
            grad = elev / dist if dist else 0
            color = "🟣" if grad > 0.08 else "🔴" if grad > 0.06 else "🟠" if grad > 0.04 else "🟡" if grad > 0.02 else "🟢"
            opciones.append(f"{color} {s['segment']['name']} ({dist/1000:.2f} km)")
        selected = st.selectbox("Elige un segmento:", opciones)
        seleccionado = segmentos[opciones.index(selected)]

        if seleccionado:
            distancia = seleccionado['segment']['distance']
            elevacion = seleccionado['segment']['elevation_high'] - seleccionado['segment']['elevation_low']
            procesar(distancia, elevacion, masa_total)
            st.subheader("📈 Perfil del Segmento")
            streams = get_streams_for_activity(actividad_id)
            if streams and "distance" in streams and "altitude" in streams:
                d = streams["distance"]
                a = streams["altitude"]
                graficar([x / 1000 for x in d[seleccionado["start_index"]:seleccionado["end_index"]]], a[seleccionado["start_index"]:seleccionado["end_index"]])
            else:
                st.warning("⚠️ No se pudo obtener el perfil de elevación.")

# === PIE DE PÁGINA ===
st.markdown("""---<p style='text-align: center; font-size: 0.8rem;'>🛠️ Desarrollado con cariño por <b>Yobwear</b> — v1.0</p>""", unsafe_allow_html=True)
