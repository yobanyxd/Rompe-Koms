import requests
import streamlit as st

CLIENT_ID = "141324"
CLIENT_SECRET = "98ab51d07e20b58141f3242e93879dd78d4dfbbc"
REDIRECT_URI = "https://rompekoms.streamlit.app/"

# === INTERCAMBIO DE CÓDIGO POR TOKEN ===
def exchange_code_for_token(code):
    url = "https://www.strava.com/oauth/token"
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code"
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        data = response.json()
        st.session_state["access_token"] = data["access_token"]
        st.session_state["refresh_token"] = data["refresh_token"]
        st.session_state["athlete"] = data["athlete"]
        return data
    else:
        print("❌ Error al obtener token:", response.text)
        return None

# === AUTENTICACIÓN Y SESIÓN ===
def get_access_token():
    return st.session_state.get("access_token")

def sesion_iniciada():
    return "access_token" in st.session_state

def cerrar_sesion_strava():
    for key in ["access_token", "refresh_token", "athlete"]:
        st.session_state.pop(key, None)

def iniciar_sesion_strava():
    # Ya no es necesario aquí; se hace todo desde app.py con el código
    pass

# === DATOS DEL USUARIO ===
def obtener_datos_atleta():
    token = get_access_token()
    if not token:
        return None
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get("https://www.strava.com/api/v3/athlete", headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

# === DATOS DE ACTIVIDADES Y SEGMENTOS ===
def get_segments_from_activity(activity_id):
    token = get_access_token()
    if not token:
        return None
    url = f"https://www.strava.com/api/v3/activities/{activity_id}?include_all_efforts=true"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data.get("segment_efforts", [])
    print("⚠️ No se encontraron segmentos.")
    return []

def get_streams_for_activity(activity_id):
    token = get_access_token()
    if not token:
        return None

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
    token = get_access_token()
    if not token:
        return None

    url = f"https://www.strava.com/api/v3/segments/{segment_id}/streams"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"keys": "distance,altitude", "key_by_type": "true"}

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"⚠️ No se pudo obtener el stream del segmento {segment_id}")
        return None
