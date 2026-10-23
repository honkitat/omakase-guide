import json, time, urllib.request, base64
import websockets.sync.client as wsc
BASE="http://127.0.0.1:9223"
def http(p): return json.loads(urllib.request.urlopen(BASE+p,timeout=10).read())
def browser_ws(): return http("/json/version")["webSocketDebuggerUrl"]
def tabs(): return http("/json/list")
def new_tab(url):
    with wsc.connect(browser_ws(),open_timeout=10) as ws:
        ws.send(json.dumps({"id":1,"method":"Target.createTarget","params":{"url":url}}))
        while True:
            m=json.loads(ws.recv(timeout=15))
            if m.get("id")==1: return m["result"]["targetId"]
def page_ws(tid):
    for t in tabs():
        if t.get("id")==tid: return t["webSocketDebuggerUrl"]
def rpc(ws,method,params=None,timeout=60):
    with wsc.connect(ws,open_timeout=10) as c:
        c.send(json.dumps({"id":1,"method":method,"params":params or {}}))
        while True:
            m=json.loads(c.recv(timeout=60))
            if m.get("id")==1: return m
def ev(ws,e):
    r=rpc(ws,"Runtime.evaluate",{"expression":e,"returnByValue":True})
    return r.get("result",{}).get("result",{}).get("value")

tid=new_tab("https://honkitat.github.io/omakase-guide/")
time.sleep(4)
ws=page_ws(tid)
for _ in range(10):
    if isinstance(ev(ws,"document.querySelectorAll('.card').length"),int): break
    time.sleep(1)
rpc(ws,"Emulation.setDeviceMetricsOverride",{"width":1100,"height":900,"deviceScaleFactor":2,"mobile":False})
time.sleep(0.5)
ev(ws,"window.scrollTo(0,1600)")  # grid area
time.sleep(4)  # let images load
r=rpc(ws,"Page.captureScreenshot",{"format":"png"})
open("/opt/data/omakase-guide/preview-restyle.png","wb").write(base64.b64decode(r["result"]["data"]))
print("screenshot saved; cards:", ev(ws,"document.querySelectorAll('.card').length"))
