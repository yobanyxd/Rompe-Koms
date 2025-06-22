from http.server import BaseHTTPRequestHandler, HTTPServer
import webbrowser
import urllib.parse
import requests

# === CONFIGURACIÓN ===
client_id = "141324"  # ⚠️ Reemplaza esto
client_secret = "98ab51d07e20b58141f3242e93879dd78d4dfbbc"  # ⚠️ Reemplaza esto
redirect_uri = "http://localhost:8000/exchange_token"

# === SERVIDOR HTTP PARA RECIBIR EL TOKEN ===
class TokenHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/exchange_token"):
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            code = params.get("code", [None])[0]

            if code:
                print(f"🔐 Código recibido: {code}")

                # Intercambiar el código por un token
                url = "https://www.strava.com/oauth/token"
                data = {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code,
                    "grant_type": "authorization_code"
                }

                response = requests.post(url, data=data)
                if response.status_code == 200:
                    token_data = response.json()
                    access_token = token_data["access_token"]
                    print(f"🔑 Token generado: {access_token}")

                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write("✅ Token recibido. Puedes cerrar esta ventana.".encode('utf-8'))
                else:
                    print("❌ Error al obtener el token.")
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write("❌ Error al obtener el token.".encode('utf-8'))
            else:
                print("❌ No se recibió código.")
                self.send_response(400)
                self.end_headers()
                self.wfile.write("❌ No se recibió código.".encode('utf-8'))

        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write("404 Not Found".encode('utf-8'))

# === INICIAR SERVIDOR ===
def run_server():
    print("🌐 Esperando token en http://localhost:8000 ...")
    webbrowser.open(
        f"https://www.strava.com/oauth/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&scope=read,activity:read_all&approval_prompt=auto"
    )

    server = HTTPServer(('localhost', 8000), TokenHandler)
    server.handle_request()

if __name__ == "__main__":
    run_server()
