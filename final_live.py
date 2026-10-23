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
for _ in range(12):
    if isinstance(ev(ws,"document.querySelectorAll('.card').length"),int): break
    time.sleep(1)
print("LIVE cards:", ev(ws,"document.querySelectorAll('.card').length"))
print("LIVE pills:", ev(ws,"[...document.querySelectorAll('#catPills .pill')].slice(1,4).map(p=>p.innerText.trim()).join(' || ')"))
print("LIVE card imgs:", ev(ws,"document.querySelectorAll('.card .imgs img').length"))
ev(ws,"document.querySelector('.card').click()")
time.sleep(0.4)
print("LIVE modal imgs:", ev(ws,"document.querySelectorAll('#modalBox .modal-imgs img').length"))
print("LIVE modal figcaption:", ev(ws,"(document.querySelector('#modalBox figcaption')||{}).innerText || 'NONE'"))
