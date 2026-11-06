"""End-to-end test of the guest submission front end.

Serves the repo on :8930, a mock receiver on :8931 (stands in for the Apps
Script /exec URL), drives the page over CDP, fills the form, submits a real
1600px-class JPEG, and reports what the receiver actually got.
"""
import base64
import functools
import http.server
import json
import os
import threading
import time
import urllib.request

import websockets.sync.client as wsc

BASE = "/opt/data/omakase-guide"
SCRATCH = "/opt/data/cache/scratch"
CDP = "http://127.0.0.1:9223"
RECEIVED = os.path.join(SCRATCH, "mock_received.json")


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


_capture = {}


class MockReceiver(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(n)
        _capture["body"] = raw.decode("utf-8", "replace")
        _capture["ct"] = self.headers.get("Content-Type")
        open(RECEIVED, "w").write(_capture["body"])
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(b'{"ok":true}')

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()


def serve():
    h1 = functools.partial(Quiet, directory=BASE)
    s1 = http.server.ThreadingHTTPServer(("127.0.0.1", 8930), h1)
    s2 = http.server.ThreadingHTTPServer(("127.0.0.1", 8931), MockReceiver)
    threading.Thread(target=s1.serve_forever, daemon=True).start()
    threading.Thread(target=s2.serve_forever, daemon=True).start()
    return s1, s2


def cdp(path):
    return json.loads(urllib.request.urlopen(CDP + path, timeout=10).read())


def new_tab(url):
    with wsc.connect(cdp("/json/version")["webSocketDebuggerUrl"], open_timeout=10) as ws:
        ws.send(json.dumps({"id": 1, "method": "Target.createTarget", "params": {"url": url}}))
        while True:
            m = json.loads(ws.recv(timeout=20))
            if m.get("id") == 1:
                return m["result"]["targetId"]


def page_ws(tid):
    for t in cdp("/json/list"):
        if t.get("id") == tid:
            return t["webSocketDebuggerUrl"]


def rpc(ws, method, params=None):
    with wsc.connect(ws, open_timeout=10) as c:
        c.send(json.dumps({"id": 1, "method": method, "params": params or {}}))
        while True:
            m = json.loads(c.recv(timeout=120))
            if m.get("id") == 1:
                return m


def ev(ws, expr):
    r = rpc(ws, "Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True})
    res = r.get("result", {})
    if res.get("exceptionDetails"):
        return {"__exc": res["exceptionDetails"].get("text"), "detail": str(res["exceptionDetails"])[:300]}
    return res.get("result", {}).get("value")


def main():
    s1, s2 = serve()
    # point the build at the mock receiver
    open(os.path.join(BASE, "guest_api.txt"), "w").write("http://127.0.0.1:8931/submit")
    os.system(f"cd {BASE} && /opt/data/trading-venv/bin/python3 build_zen.py")

    img = os.path.join(SCRATCH, "test_upload.jpg")
    os.system(f"cp {BASE}/images/dish/tamago.jpg {img}")
    b64 = base64.b64encode(open(img, "rb").read()).decode()
    print("test image bytes:", os.path.getsize(img))

    tid = new_tab("http://127.0.0.1:8930/index.html")
    time.sleep(4)
    ws = page_ws(tid)
    rpc(ws, "Emulation.setDeviceMetricsOverride", {"width": 1280, "height": 900, "deviceScaleFactor": 1, "mobile": False})
    time.sleep(2)

    print("API wired:", ev(ws, "typeof GUEST_API + ':' + GUEST_API"))
    print("upload button visible:", ev(ws, "!document.getElementById('upBtn').hidden"))
    print("button label:", ev(ws, "document.getElementById('upBtn').textContent"))

    ev(ws, "document.getElementById('upBtn').click()")
    time.sleep(0.6)
    print("panel open:", ev(ws, "document.getElementById('subOverlay').classList.contains('open')"))
    print("fish options:", ev(ws, "document.getElementById('fishList').children.length"))

    setup = f"""(()=>{{
      const d=atob('{b64}'); const u=new Uint8Array(d.length);
      for(let i=0;i<d.length;i++) u[i]=d.charCodeAt(i);
      const f=new File([u],'test.jpg',{{type:'image/jpeg'}});
      const dt=new DataTransfer(); dt.items.add(f);
      document.getElementById('subFile').files=dt.files;
      document.getElementById('subFishInput').value='玉子';
      document.getElementById('subVenue').value='測試店 Test Sushi';
      document.getElementById('subComment').value='測試評語：玉子燒偏甜，溫度剛好。';
      document.getElementById('subName').value='tester';
      return document.getElementById('subFile').files.length;
    }})()"""
    print("file attached:", ev(ws, setup))

    start = time.time()
    ev(ws, "sendSubmission()")
    for _ in range(30):
        if _capture.get("body"):
            break
        time.sleep(0.5)
    print("waited %.1fs, received: %s bytes" % (time.time() - start, len(_capture.get("body", ""))))
    print("post message text:", ev(ws, "document.getElementById('subMsg').textContent"))

    r = rpc(ws, "Page.captureScreenshot", {"format": "jpeg", "quality": 88})
    open(os.path.join(SCRATCH, "submit_ui.jpg"), "wb").write(base64.b64decode(r["result"]["data"]))

    # inspect payload
    body = _capture.get("body", "")
    if body:
        p = json.loads(body)
        print("payload keys:", sorted(p.keys()))
        print("fish/venue/name:", p["fish"], "|", p["venue"], "|", p.get("submitter"))
        print("comment:", p["comment"])
        head, b = p["image"].split(",", 1)
        raw = base64.b64decode(b)
        print("image dataURL header:", head, "| decoded bytes:", len(raw))
        open(os.path.join(SCRATCH, "roundtrip.jpg"), "wb").write(raw)
        print("content-type header sent:", _capture.get("ct"))

    # restore
    open(os.path.join(BASE, "guest_api.txt"), "w").write("")
    os.system(f"cd {BASE} && /opt/data/trading-venv/bin/python3 build_zen.py")
    s1.shutdown()
    s2.shutdown()


if __name__ == "__main__":
    main()
