import requests
import json
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import os

CLIENT_ID = "141324"
CLIENT_SECRET = "98ab51d07e20b58141f3242e93879dd78d4dfbbc"
REDIRECT_URI = "https://rompekoms.streamlit.app/"
TOKEN_FILE = "strava_token.json"

# === SERVIDOR PARA AUTENTICACIÓN LOCAL ===
class TokenHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if "/exchange_token" in self.path:
            code = self.path.split("code=")[-1].split("&")[0]
            token_data = exchange_code_for_token(code)
            if token_data:
                with open(TOKEN_FILE, "w") as f:
                    json.dump(token_data, f)
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write("""
                <html>
                <head>
                    <title>Autenticación exitosa</title>
                    <script>
                        setTimeout(() => {
                            window.close();
                        }, 2000);
                    </script>
                </head>
                <body style='font-family: sans-serif;'>
                    <h2>✅ Autenticación completada.</h2>
                    <p>Esta ventana se cerrará automáticamente en unos segundos.</p>
                </body>
                </html>
                """.encode("utf-8"))
            else:
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write("❌ No se pudo obtener el token.".encode("utf-8"))

def run_server():
    server = HTTPServer(('localhost', 8000), TokenHandler)
    print("🌐 Esperando autenticación en http://localhost:8000...")
    server.handle_request()

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
        return response.json()
    else:
        print("❌ Error al obtener token:", response.text)
        return None

# === TOKEN MANAGEMENT ===
def cargar_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            return json.load(f).get("access_token")
    return None

def get_access_token():
    token = cargar_token()
    if token:
        return token
    else:
        threading.Thread(target=run_server).start()
        auth_url = (
            f"https://www.strava.com/oauth/authorize?client_id={CLIENT_ID}"
            f"&redirect_uri={REDIRECT_URI}&response_type=code&scope=activity:read_all"
        )
        webbrowser.open(auth_url)

# === FUNCIONES DE USUARIO ===
def iniciar_sesion_strava():
    get_access_token()

def sesion_iniciada():
    return os.path.exists(TOKEN_FILE)

def cerrar_sesion_strava():
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)

def obtener_datos_atleta():
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get("https://www.strava.com/api/v3/athlete", headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

# === DATOS DE ACTIVIDADES Y SEGMENTOS ===
def get_segments_from_activity(activity_id):
    token = get_access_token()
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
