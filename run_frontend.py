import http.server
import socketserver
import webbrowser
import threading
import time
import os
from pathlib import Path

# 前端目录
FRONTEND_DIR = Path(__file__).parent

# 前端端口
PORT = 5500

class FrontendHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)
    
    def end_headers(self):
        # 添加CORS头
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()

def open_browser():
    """延迟打开浏览器"""
    time.sleep(1)
    webbrowser.open(f'http://localhost:{PORT}')

def start_frontend_server():
    """启动前端服务器"""
    # 切换到前端目录
    os.chdir(FRONTEND_DIR)
    
    with socketserver.TCPServer(("", PORT), FrontendHandler) as httpd:
        print(f"前端服务器启动成功!")
        print(f"访问地址: http://localhost:{PORT}")
        print(f"前端目录: {FRONTEND_DIR}")
        print("=" * 50)
        
        # 在新线程中打开浏览器
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n前端服务器已停止")

if __name__ == "__main__":
    start_frontend_server()