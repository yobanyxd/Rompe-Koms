import requests
import re

# === DATOS DE AUTORIZACIÓN ===
access_token = "cc3d8b59bfdb2f7b0c7169b8e5b3f3cb939d26dd"

# === LINK DE STRAVA (ACTIVIDAD COMPLETA) ===
link_strava = "https://www.strava.com/activities/14868598235"

# === EXTRAER ID DE ACTIVIDAD ===
match = re.search(r'/activities/(\d+)', link_strava)
if not match:
    print("❌ No se pudo extraer el ID de actividad.")
    exit()

activity_id = match.group(1)
print(f"🔍 Analizando actividad {activity_id}...")

# === OBTENER DETALLES DE LA ACTIVIDAD ===
url = f"https://www.strava.com/api/v3/activities/{activity_id}?include_all_efforts=true"
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(url, headers=headers)

if response.status_code != 200:
    print(f"❌ Error {response.status_code}: {response.text}")
    exit()

data = response.json()

# === MOSTRAR TODOS LOS SEGMENTOS ===
segmentos = data.get("segment_efforts", [])

if not segmentos:
    print("❌ No se encontraron segmentos en esta actividad.")
    exit()

print(f"✅ {len(segmentos)} segmentos encontrados:")
for s in segmentos:
    nombre = s['name']
    distancia = s['distance'] / 1000
    elevacion = s['segment']['elevation_high'] - s['segment']['elevation_low']
    pendiente = round(elevacion / distancia / 10, 1)
    print(f"➡️ {nombre}: {distancia:.2f} km, pendiente aprox: {pendiente}%")
