"""Render the approved-submission block locally and screenshot it."""
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


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


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
        return {"__exc": res["exceptionDetails"].get("text")}
    return res.get("result", {}).get("value")


def main():
    h = functools.partial(Quiet, directory=BASE)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 8932), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    backup = json.load(open(f"{BASE}/guest.json"))
    json.dump([{"fish": "玉子", "venue": "測試店 Test Sushi", "comment": "玉子燒外層焦香、內裡仍軟，甜度剋制。",
                "date": "2026-10-29", "by": "@tester", "photo": "images/dish/tamago.jpg"}],
              open(f"{BASE}/guest.json", "w"), ensure_ascii=False, indent=1)
    os.system(f"cd {BASE} && /opt/data/trading-venv/bin/python3 build_zen.py")

    tid = new_tab("http://127.0.0.1:8932/index.html")
    time.sleep(4)
    ws = page_ws(tid)
    rpc(ws, "Emulation.setDeviceMetricsOverride", {"width": 1180, "height": 980, "deviceScaleFactor": 1, "mobile": False})
    time.sleep(2)
    idx = ev(ws, "FISH.findIndex(f=>f.j==='玉子')")
    print("index:", idx)
    ev(ws, f"openM({idx})")
    time.sleep(1.6)
    print("guest block:", ev(ws, "document.querySelectorAll('.guest .gitem').length"))
    print("submit link:", ev(ws, "!!document.querySelector('.msubmit a')"))
    ev(ws, "(()=>{const g=document.querySelector('.guest'); if(g) g.scrollIntoView({block:'center'}); const b=document.getElementById('mbox'); if(b) b.scrollTop=b.scrollHeight; return 1;})()")
    time.sleep(1.2)
    r = rpc(ws, "Page.captureScreenshot", {"format": "jpeg", "quality": 90})
    open(os.path.join(SCRATCH, "guest_block.jpg"), "wb").write(base64.b64decode(r["result"]["data"]))
    print("shot ok")

    json.dump(backup, open(f"{BASE}/guest.json", "w"), ensure_ascii=False, indent=1)
    os.system(f"cd {BASE} && /opt/data/trading-venv/bin/python3 build_zen.py")
    srv.shutdown()


if __name__ == "__main__":
    main()
