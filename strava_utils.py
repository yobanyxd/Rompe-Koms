import requests
import os
import json

# Configuración de la app de Strava
CLIENT_ID = "141324"
CLIENT_SECRET = "98ab51d07e20b58141f3242e93879dd78d4dfbbc"
REDIRECT_URI = "https://rompekoms.streamlit.app/"
TOKEN_FILE = "strava_token.json"

def exchange_code_for_token(code):
    """
    Intercambia el código de autorización por un access_token de Strava.
    """
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
    """
    Carga el access_token si ya existe.
    """
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            token_data = json.load(f)
        return token_data.get("access_token")
    return None

def cargar_token():
    """
    Devuelve solo el token sin volver a pedir nada.
    """
    return get_access_token()

def iniciar_sesion_strava():
    """
    Ya no es necesaria en versión en la nube, porque se inicia desde el enlace del sidebar.
    """
    pass

def sesion_iniciada():
    """
    Devuelve True si el archivo de token existe.
    """
    return os.path.exists(TOKEN_FILE)

def cerrar_sesion_strava():
    """
    Elimina el token guardado.
    """
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)

def obtener_datos_atleta():
    """
    Consulta la API de Strava para obtener datos del atleta autenticado.
    """
    token = get_access_token()
    if not token:
        return None

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get("https://www.strava.com/api/v3/athlete", headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

def get_segments_from_activity(activity_id):
    """
    Obtiene los esfuerzos de segmento dentro de una actividad específica.
    """
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
    """
    Obtiene los datos de distancia y altitud de toda la actividad.
    """
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
    """
    Obtiene el perfil de altimetría de un segmento.
    """
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
