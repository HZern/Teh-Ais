import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from config_scanner import scan_cloud_configurations


HOST = "127.0.0.1"
PORT = 8000


class SecurityBackendHandler(BaseHTTPRequestHandler):
    """
    Simple backend server for the cloud security monitoring MVP.

    Routes:
    - GET /        : health check
    - GET /alerts  : runs scanner and returns latest warning/danger alerts
    """

    def send_json_response(self, data, status_code=200):
        """
        Sends a JSON response with CORS enabled so the frontend can call it.
        """
        response = json.dumps(data, indent=4)

        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

        self.wfile.write(response.encode("utf-8"))

    def do_OPTIONS(self):
        """
        Handles browser CORS preflight requests.
        """
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        """
        Handles GET requests from the frontend.
        """
        if self.path == "/":
            self.send_json_response({
                "message": "Cloud Security Monitoring Backend is running"
            })

        elif self.path == "/alerts":
            alerts = scan_cloud_configurations()

            self.send_json_response({
                "alerts": alerts,
                "count": len(alerts),
                "message": "Scanner ran successfully and returned latest alerts"
            })

        else:
            self.send_json_response({
                "error": "Endpoint not found"
            }, status_code=404)


def run_backend():
    """
    Starts the local backend server.
    """
    server = HTTPServer((HOST, PORT), SecurityBackendHandler)

    print(f"Security backend running at http://{HOST}:{PORT}")
    print(f"Alerts endpoint: http://{HOST}:{PORT}/alerts")

    server.serve_forever()


if __name__ == "__main__":
    run_backend()