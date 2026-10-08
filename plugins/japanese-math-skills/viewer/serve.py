"""Local-only static viewer. Run from any directory; Ctrl-C stops the server."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import build

class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control','no-cache')
        self.send_header('X-Content-Type-Options','nosniff')
        super().end_headers()
    def list_directory(self,path):
        self.send_error(404);return None

def main():
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8769);a=p.parse_args()
    build.build()
    server=ThreadingHTTPServer(('127.0.0.1',a.port),partial(Handler,directory=str(Path(__file__).parent/'dist')))
    print(f'Japanese corpus: http://127.0.0.1:{a.port}/',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
if __name__=='__main__':main()
