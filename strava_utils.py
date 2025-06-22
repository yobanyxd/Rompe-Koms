import requests
import os
import json
import webbrowser
import urllib.parse

# CONFIG DE STRAVA
CLIENT_ID = "141324"
CLIENT_SECRET = "98ab51d07e20b58141f3242e93879dd78d4dfbbc"
REDIRECT_URI = "https://rompekoms.streamlit.app/"
TOKEN_FILE = "strava_token.json"

def intercambiar_codigo_por_token(code):
    url = "https://www.strava.com/oauth/token"
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code"
    }
    response = requests.post(url, data=payload)
    
    if response.status_code == 200:
        token_data = response.json()
        with open(TOKEN_FILE, "w") as f:
            json.dump(token_data, f)
        return token_data
    else:
        print("❌ Error al obtener token:", response.text)
        return None

def get_access_token():
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
    token = get_access_token()
    if not token:
        return None
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get("https://www.strava.com/api/v3/athlete", headers=headers)
    return response.json() if response.status_code == 200 else None

def get_segments_from_activity(activity_id):
    token = get_access_token()
    if not token:
        return None
    url = f"https://www.strava.com/api/v3/activities/{activity_id}?include_all_efforts=true"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    return response.json().get("segment_efforts", []) if response.status_code == 200 else []

def get_streams_for_activity(activity_id):
    token = get_access_token()
    if not token:
        return None
    url = f"https://www.strava.com/api/v3/activities/{activity_id}/streams"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"keys": "distance,altitude", "key_by_type": "true"}
    response = requests.get(url, headers=headers, params=params)
    return response.json() if response.status_code == 200 else None

def get_streams_for_segment(segment_id):
    token = get_access_token()
    if not token:
        return None
    url = f"https://www.strava.com/api/v3/segments/{segment_id}/streams"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"keys": "distance,altitude", "key_by_type": "true"}
    response = requests.get(url, headers=headers, params=params)
    return response.json() if response.status_code == 200 else None

def iniciar_sesion_strava():
    url = "https://www.strava.com/oauth/authorize"
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": "read,activity:read_all",
        "approval_prompt": "auto"
    }
    full_url = f"{url}?{urllib.parse.urlencode(params)}"
    webbrowser.open(full_url)
