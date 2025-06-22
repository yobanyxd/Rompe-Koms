import os
import requests
import json
from urllib.parse import urlencode

CLIENT_ID = "141324"
CLIENT_SECRET = "98ab51d07e20b58141f3242e93879dd78d4dfbbc"
REDIRECT_URI = "https://rompekoms.streamlit.app"  # la URL de tu app en Streamlit
TOKEN_FILE = "strava_token.json"

def get_auth_url():
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "approval_prompt": "auto",
        "scope": "read,activity:read_all"
    }
    return f"https://www.strava.com/oauth/authorize?{urlencode(params)}"

def exchange_code_for_token(code):
    response = requests.post("https://www.strava.com/oauth/token", data={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
    })

    if response.status_code == 200:
        token_data = response.json()
        with open(TOKEN_FILE, "w") as f:
            json.dump(token_data, f)
        return token_data
    else:
        print("❌ Error intercambiando código por token:", response.text)
        return None

def cargar_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            return json.load(f).get("access_token")
    return None

def sesion_iniciada():
    return os.path.exists(TOKEN_FILE)

def cerrar_sesion_strava():
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)

def obtener_datos_atleta():
    token = cargar_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get("https://www.strava.com/api/v3/athlete", headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

def get_segments_from_activity(activity_id):
    token = cargar_token()
    url = f"https://www.strava.com/api/v3/activities/{activity_id}?include_all_efforts=true"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data.get("segment_efforts", [])
    print("⚠️ No se encontraron segmentos.")
    return []

def get_streams_for_activity(activity_id):
    token = cargar_token()
    url = f"https://www.strava.com/api/v3/activities/{activity_id}/streams"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"keys": "distance,altitude", "key_by_type": "true"}

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print("⚠️ No se pudo obtener el stream de la actividad.")
        return None

def get_streams_for_segment(segment_id):
    token = cargar_token()
    url = f"https://www.strava.com/api/v3/segments/{segment_id}/streams"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"keys": "distance,altitude", "key_by_type": "true"}

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"⚠️ No se pudo obtener el stream del segmento {segment_id}")
        return None
