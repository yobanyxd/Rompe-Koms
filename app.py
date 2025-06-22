import streamlit as st
import gpxpy
import os
import math
import matplotlib.pyplot as plt
from urllib.parse import urlencode

from strava_utils import (
    intercambiar_codigo_por_token,
    sesion_iniciada,
    cerrar_sesion_strava,
    obtener_datos_atleta,
    get_segments_from_activity,
    get_streams_for_activity,
)

# === CONFIGURACIÓN GENERAL ===
st.set_page_config(page_title="Calculadora de Segmentos 🚴‍♂️", layout="centered")

# — Captura el “code” que Strava devuelve y cambia el token
if (code := st.query_params.get("code")):
    info = intercambiar_codigo_por_token(code[0])
    if info:
        st.success("✅ ¡Sesión iniciada correctamente!")
        # Limpia la query string y recarga
        st.experimental_set_query_params()
        st.experimental_rerun()
    else:
        st.error("❌ Hubo un problema al iniciar sesión con Strava.")

# — Cabecera y logo según tema
tema = st.get_option("theme.base")
logo = "logo_dark.png" if tema == "dark" else "logo_light.png"
c1, c2 = st.columns([4,1])
with c1:
    st.markdown("## 🔥 CALCULADORA ROMPE KOM'S")
    st.caption("Analiza tus segmentos favoritos usando tu FTP, peso y tipo de bici.")
with c2:
    if os.path.exists(logo):
        st.image(logo, width=100)

st.markdown("---")

# === SELECCIÓN DE MODO ===
modo = st.radio(
    "Selecciona modo de entrada:",
    ("📂 Archivo GPX", "🗺️ Segmento de Strava"),
    horizontal=True
)

# === OPCIÓN DE LOGIN (solo para Strava) ===
login_strava = False
if modo == "🗺️ Segmento de Strava":
    login_strava = st.checkbox("🔐 Iniciar sesión con Strava (opcional)")

# Si el usuario pidió login, muestro flujo OAuth o datos del atleta
if login_strava:
    if sesion_iniciada():
        atleta = obtener_datos_atleta()
        if atleta:
            a1,a2 = st.columns([1,4])
            a1.image(atleta["profile"], width=50)
            a2.markdown(f"**{atleta['firstname']} {atleta['lastname']}**")
            if st.button("🔓 Cerrar sesión con Strava"):
                cerrar_sesion_strava()
                st.experimental_rerun()
        else:
            st.warning("⚠️ Error obteniendo datos. Fuerza cierre de sesión:")
            if st.button("Forzar cierre de sesión"):
                cerrar_sesion_strava()
                st.experimental_rerun()
    else:
        params = urlencode({
            "client_id":"141324",
            "response_type":"code",
            "redirect_uri":"https://rompekoms.streamlit.app/",
            "approval_prompt":"auto",
            "scope":"read,activity:read_all",
        })
        st.markdown(
            f"[🔗 Iniciar sesión con Strava](https://www.strava.com/oauth/authorize?{params})",
            unsafe_allow_html=True
        )

st.markdown("---")

# === DATOS BÁSICOS ===
p1,p2 = st.columns(2)
peso_user = p1.number_input("🏋️ Peso ciclista (kg)", 62.0)
peso_bici = p2.number_input("🚲 Peso bici + equipo (kg)", 8.0)
altura    = st.number_input("📏 Altura (cm)", 170)
ftp       = st.number_input("⚡ FTP (watts)", 275.0)
t_obj     = st.text_input("⏱️ Tiempo objetivo mm:ss (opcional)", "")

# === PARÁMETROS AERODINÁMICOS ===
tipo = st.selectbox("Tipo de bicicleta", ["Ruta","Triatlón","MTB","Urbana"])
param = {"Ruta":(.32,.004),"Triatlón":(.25,.0035),"MTB":(.4,.008),"Urbana":(.38,.006)}[tipo]
CdA, Crr = param
rho, g = 1.225, 9.81

# === FUNCIONES DE CÁLCULO y GRAFICO ===
def estimar_potencia(dist, elev, tiempo, masa):
    v = dist/tiempo
    Pg = masa*g*(elev/dist)*v
    Pr = masa*g*Crr*v
    Pa = .5*rho*CdA*v**3
    return Pg+Pr+Pa

def graficar(xs, ys):
    plt.figure(figsize=(8,3))
    plt.plot(xs, ys)
    plt.xlabel("Distancia (km)")
    plt.ylabel("Altura (m)")
    st.pyplot(plt)

def procesar(dist, elev, masa):
    st.markdown(f"**Distancia:** {dist/1000:.2f} km   **Desnivel:** {elev:.0f} m")
    if t_obj:
        mm, ss = (map(int, t_obj.split(":")) if ":" in t_obj else (int(t_obj),0))
        t_seg = mm*60+ss
        p_req = estimar_potencia(dist,elev,t_seg,masa)
        st.success(f"Necesitas ~ {p_req:.0f} W  ({p_req/peso_user:.2f} W/kg)")
    else:
        p90 = ftp*0.9
        st.info(f"Con 90% FTP ({p90:.0f} W) ≈ {(dist/( (lambda P: next((v for v in [i/10 for i in range(1,1001)] if abs((masa*g*(elev/dist)*v + masa*g*Crr*v + .5*rho*CdA*v**3)-P)<.1),1) )(p90)))/60:.1f} min")

# === GPX o STRAVA ===
if modo=="📂 Archivo GPX":
    gpx_file = st.file_uploader("📁 Sube tu GPX", type="gpx")
    if gpx_file:
        gpx = gpxpy.parse(gpx_file.read().decode())
        pts, td, te = [],0,0
        for tr in gpx.tracks:
            for seg in tr.segments:
                pts += seg.points
                for i in range(1,len(seg.points)):
                    d = seg.points[i-1].distance_3d(seg.points[i])
                    e = max(0, seg.points[i].elevation-seg.points[i-1].elevation)
                    td+=d; te+=e
        xs, ys, acc = [],[],0
        for i in range(1,len(pts)):
            d=pts[i-1].distance_3d(pts[i]); acc+=d
            xs.append(acc/1000); ys.append(pts[i].elevation)
        masa = peso_user + peso_bici
        graficar(xs,ys)
        procesar(td,te,masa)

elif modo=="🗺️ Segmento de Strava":
    act = st.text_input("🔗 ID o URL del segmento Strava")
    if act:
        sid = act.split("/")[-1]
        segs = get_segments_from_activity(sid)
        if not segs:
            st.error("❌ No se encontraron segmentos.")
        else:
            masa = peso_user + peso_bici
            orden = sorted(
                segs,
                key=lambda s: -estimar_potencia(
                    s["segment"]["distance"],
                    s["segment"]["elevation_high"]-s["segment"]["elevation_low"],
                    s["segment"]["distance"]/(ftp*0.9),
                    masa
                )
            )
            opts = [f"🎯 {s['segment']['name']} ({s['segment']['distance']/1000:.2f} km)"
                    for s in orden]
            sel = st.selectbox("Elige segmento", opts)
            S   = orden[opts.index(sel)]["segment"]
            d,e = S["distance"], S["elevation_high"]-S["elevation_low"]
            graficar(
                [v/1000 for v in get_streams_for_activity(sid)["distance"]["data"][orden[opts.index(sel)]["start_index"]:orden[opts.index(sel)]["end_index"]]],
                get_streams_for_activity(sid)["altitude"]["data"][orden[opts.index(sel)]["start_index"]:orden[opts.index(sel)]["end_index"]]
            )
            procesar(d,e,masa)

# === PIE DE PÁGINA ===
st.markdown("---")
st.caption("🛠️ Desarrollado con cariño por **Yobwear** — v1.0")
