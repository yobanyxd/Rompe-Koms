import re
import requests

# === ACCESS TOKEN (debe estar actualizado) ===
access_token = "cc3d8b59bfdb2f7b0c7169b8e5b3f3cb939d26dd"

# === LINK DE ESFUERZO (NO del segmento base) ===
link_strava = "https://www.strava.com/activities/14868598235/segments/3371455784447147262"

# === Extraer IDs ===
match = re.search(r'/activities/(\d+)/segments/(\d+)', link_strava)
if not match:
    print("❌ No se pudo extraer los IDs.")
    exit()

activity_id, effort_id = match.groups()
print(f"🔎 Actividad ID: {activity_id}")
print(f"🧪 Esfuerzo ID: {effort_id}")

# === Consultar esfuerzo (segment effort) ===
url = f"https://www.strava.com/api/v3/segment_efforts/{effort_id}"
headers = {
    "Authorization": f"Bearer {access_token}"
}
response = requests.get(url, headers=headers)

if response.status_code == 200:
    effort = response.json()
    segment = effort['segment']
    print("✅ Segmento encontrado a través del esfuerzo:")
    print(f"🏷️ Nombre: {segment['name']}")
    print(f"📏 Distancia: {segment['distance'] / 1000:.2f} km")
    print(f"📈 Pendiente media: {segment['average_grade']}%")
    print(f"📉 Elevación mínima: {segment['elevation_low']} m")
    print(f"⛰️ Elevación máxima: {segment['elevation_high']} m")
    print(f"📊 Categoría: {segment['climb_category']}")
else:
    print(f"❌ Error {response.status_code}: {response.text}")
