import os
import json
import subprocess
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

APP_DIR = os.path.dirname(os.path.abspath(__file__))

class CustomHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=APP_DIR, **kwargs)

    def do_POST(self):
        if self.path == '/api/export':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                save_path = os.path.join(APP_DIR, "CS2_NewTown_Layout.json")
                with open(save_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                res = json.dumps({"status": "success", "path": save_path})
                self.wfile.write(res.encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                res = json.dumps({"status": "error", "message": str(e)})
                self.wfile.write(res.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # 침묵 모드

def launch_app_window(port):
    url = f"http://127.0.0.1:{port}/index.html"
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    ]
    edge_exe = next((p for p in edge_paths if os.path.exists(p)), None)

    if edge_exe:
        # Edge 독립 데스크톱 앱 모드 실행 (주소창, 탭 없는 네이티브 창)
        cmd = [edge_exe, f"--app={url}", "--window-size=1440,900"]
        subprocess.Popen(cmd)
    else:
        if not webbrowser.open(url):
            raise RuntimeError(f"브라우저를 열 수 없습니다. 직접 열어 주세요: {url}")

def main():
    # 운영체제가 빈 포트를 선택하므로 다른 앱의 서버와 충돌하지 않는다.
    with ThreadingHTTPServer(('127.0.0.1', 0), CustomHandler) as server:
        port = server.server_address[1]
        print(f"[K-City Planner] Server running on http://127.0.0.1:{port}", flush=True)
        launch_app_window(port)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("Shutting down...")

if __name__ == '__main__':
    main()
