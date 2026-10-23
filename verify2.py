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
    if "exceptionDetails" in r.get("result",{}): return {"ERR":r["result"]["exceptionDetails"].get("text")}
    return r.get("result",{}).get("result",{}).get("value")

tid=new_tab("file:///opt/data/omakase-guide/index.html")
time.sleep(3)
ws=page_ws(tid)
for _ in range(10):
    if isinstance(ev(ws,"document.querySelectorAll('.card').length"),int): break
    time.sleep(1)
print("cards:", ev(ws,"document.querySelectorAll('.card').length"))
print("category pills:", ev(ws,"[...document.querySelectorAll('#catPills .pill')].map(p=>p.innerText.trim()).join(' | ')"))
print("card imgs:", ev(ws,"document.querySelectorAll('.card .imgs img').length"))
print("card chip sample:", ev(ws,"document.querySelector('.card .chips .chip') ? document.querySelector('.card .chips .chip').innerText : 'NONE'"))
# open a card, check modal chip + figcaption
ev(ws,"document.querySelector('.card').click()")
time.sleep(0.5)
print("modal chip:", ev(ws,"document.querySelector('#modalBox .meta .chip') ? document.querySelector('#modalBox .meta .chip').innerText : 'NONE'"))
print("modal figcaption:", ev(ws,"(document.querySelector('#modalBox figcaption')||{}).innerText || 'NONE'"))

print("modal-imgs count:", ev(ws,"document.querySelectorAll('#modalBox .modal-imgs').length"))
print("modal imgs:", ev(ws,"document.querySelectorAll('#modalBox .modal-imgs img').length"))
print("modal figures:", ev(ws,"document.querySelectorAll('#modalBox .modal-imgs figure').length"))
print("modalBox html len:", ev(ws,"document.getElementById('modalBox').innerHTML.length"))
