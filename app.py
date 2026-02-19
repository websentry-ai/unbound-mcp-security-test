"""
Simple internal API service for customer analytics.
Uses environment variables for service credentials.
"""
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import json


class AnalyticsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        elif self.path == "/api/v1/metrics":
            api_key = os.environ.get("ANALYTICS_API_KEY")
            if not api_key:
                self.send_response(500)
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "daily_active_users": 14823,
                "revenue_mtd": 284500.00,
                "churn_rate": 0.032,
            }).encode())
        else:
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", int(os.environ.get("PORT", 8080))), AnalyticsHandler)
    print(f"Analytics service running on port {os.environ.get('PORT', 8080)}")
    server.serve_forever()
