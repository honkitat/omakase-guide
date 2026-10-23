import json, time, urllib.request
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
# force all lazy images to load by scrolling through page in steps
ev(ws,"window.scrollTo(0,0)")
for y in range(0, 12000, 800):
    ev(ws,f"window.scrollTo(0,{y})")
    time.sleep(0.4)
ev(ws,"window.scrollTo(0,0)")
time.sleep(25)  # let all load
res = ev(ws, "[...document.querySelectorAll('.card .imgs img')].filter(i=>i.naturalWidth===0).map(i=>i.alt+' :: '+(i.currentSrc||i.src).slice(0,70)).join('\\n')")
print("broken count:", len(res.split(chr(10))) if res else 0)
print(res if res else "ALL LOADED")
