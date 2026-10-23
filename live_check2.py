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
            m=json.loads(c.recv(timeout=timeout))
            if m.get("id")==1: return m
def ev(ws,e):
    r=rpc(ws,"Runtime.evaluate",{"expression":e,"returnByValue":True})
    return r.get("result",{}).get("result",{}).get("value")

tid=new_tab("https://honkitat.github.io/omakase-guide/")
time.sleep(5)
ws=page_ws(tid)
for _ in range(12):
    c=ev(ws,"document.querySelectorAll('.card').length")
    if isinstance(c,int) and c>0: break
    time.sleep(1)
print("LIVE cards:", c)
print("LIVE imgs:", ev(ws,"document.querySelectorAll('.card .imgs img').length"))
print("LIVE placeholders:", ev(ws,"document.querySelectorAll('.card .imgs .noimg').length"))
# scroll to top, wait for first images to load, check naturalWidth
ev(ws,"window.scrollTo(0,0)")
time.sleep(5)
print("first 6 card imgs naturalWidth:", ev(ws,"[...document.querySelectorAll('.card .imgs img')].slice(0,6).map(i=>i.naturalWidth).join(',')"))
# scroll through to trigger lazy load
ev(ws,"window.scrollTo(0,document.body.scrollHeight)")
time.sleep(3)
ev(ws,"window.scrollTo(0,0)")
time.sleep(2)
print("broken after scroll (naturalWidth 0):", ev(ws,"[...document.querySelectorAll('.card .imgs img')].filter(i=>i.naturalWidth===0).length"))
