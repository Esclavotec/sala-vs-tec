"""Servidor falso que imita la API REST de Firebase Realtime Database
(GET / PUT / DELETE y transmisión EventSource) para probar la app sin internet."""
import json, threading, time, sys
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

DB = {}
LOCK = threading.Condition()
VERSION = [0]

def parts(p):
    p = p.split('?')[0]
    if p.endswith('.json'): p = p[:-5]
    return [x for x in p.split('/') if x]

def get(ps):
    o = DB
    for k in ps:
        if not isinstance(o, dict) or k not in o: return None
        o = o[k]
    return o

def setv(ps, val):
    o = DB
    for k in ps[:-1]:
        if not isinstance(o.get(k), dict): o[k] = {}
        o = o[k]
    if val is None: o.pop(ps[-1], None)
    else: o[ps[-1]] = val

def resolve(v):
    if isinstance(v, dict):
        if v == {'.sv': 'timestamp'}: return int(time.time() * 1000)
        return {k: resolve(x) for k, x in v.items()}
    return v

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET,PUT,DELETE,PATCH,OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
    def do_OPTIONS(self):
        self.send_response(204); self.cors(); self.end_headers()
    def reply(self, obj):
        b = json.dumps(obj).encode()
        self.send_response(200); self.cors()
        self.send_header('Content-Type', 'application/json'); self.send_header('Content-Length', str(len(b)))
        self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        ps = parts(self.path)
        if 'text/event-stream' in self.headers.get('Accept', ''):
            self.send_response(200); self.cors()
            self.send_header('Content-Type', 'text/event-stream'); self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            seen = -1
            try:
                while True:
                    with LOCK:
                        if seen == VERSION[0]: LOCK.wait(timeout=15)
                        cur = VERSION[0]; val = get(ps)
                    if cur != seen:
                        seen = cur
                        self.wfile.write(('event: put\ndata: ' + json.dumps({'path': '/', 'data': val}) + '\n\n').encode())
                    else:
                        self.wfile.write(b'event: keep-alive\ndata: null\n\n')
                    self.wfile.flush()
            except Exception:
                return
        with LOCK: v = get(ps)
        self.reply(v)
    def body(self):
        n = int(self.headers.get('Content-Length') or 0)
        return json.loads(self.rfile.read(n) or b'null')
    def do_PUT(self):
        ps = parts(self.path); v = resolve(self.body())
        with LOCK: setv(ps, v); VERSION[0] += 1; LOCK.notify_all()
        self.reply(v)
    def do_DELETE(self):
        ps = parts(self.path)
        with LOCK: setv(ps, None); VERSION[0] += 1; LOCK.notify_all()
        self.reply(None)

if __name__ == '__main__':
    ThreadingHTTPServer(('127.0.0.1', int(sys.argv[1]) if len(sys.argv) > 1 else 8001), H).serve_forever()
