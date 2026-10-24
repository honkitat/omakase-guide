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
def rpc(ws,method,params=None):
    with wsc.connect(ws,open_timeout=10) as c:
        c.send(json.dumps({"id":1,"method":method,"params":params or {}}))
        while True:
            m=json.loads(c.recv(timeout=90))
            if m.get("id")==1: return m
def ev(ws,e):
    r=rpc(ws,"Runtime.evaluate",{"expression":e,"returnByValue":True})
    if "exceptionDetails" in r.get("result",{}): return {"ERR":str(r["result"]["exceptionDetails"])[:200]}
    return r.get("result",{}).get("result",{}).get("value")
def shot(ws,path):
    r=rpc(ws,"Page.captureScreenshot",{"format":"jpeg","quality":80})
    open(path,"wb").write(base64.b64decode(r["result"]["data"]))

tid=new_tab("file:///opt/data/omakase-guide/index.html")
time.sleep(3)
ws=page_ws(tid)
rpc(ws,"Emulation.setDeviceMetricsOverride",{"width":1280,"height":1000,"deviceScaleFactor":1,"mobile":False})
for _ in range(15):
    if (ev(ws,"document.querySelectorAll('.card').length") or 0)>0: break
    time.sleep(1)
time.sleep(1)

# rigorous crop check: rendered box aspect vs natural aspect
print(ev(ws,"""(()=>{
  const out=[];
  document.querySelectorAll('.card img').forEach(i=>{
    const r=i.getBoundingClientRect();
    if(!i.naturalWidth) return;
    out.push({f:i.getAttribute('src').split('/').pop(),
              box:+(r.width/r.height).toFixed(3),
              nat:+(i.naturalWidth/i.naturalHeight).toFixed(3)});
  });
  const bad=out.filter(o=>Math.abs(o.box-o.nat)>0.01);
  return {withPhoto:out.length, cropped:bad.length, samples:bad.slice(0,8)};
})()"""))

# screenshots of a photo-dense area: filter to a category then capture
print(ev(ws,"""(()=>{
  const cards=[...document.querySelectorAll('.card')];
  const idx=cards.findIndex(c=>c.querySelector('img'));
  return idx;
})()"""))
for n,y in enumerate([0,1400,2800]):
    ev(ws,f"window.scrollTo(0,{y})"); time.sleep(0.6)
    shot(ws,f"/opt/data/cache/scratch/frames/after_{n}.jpg")
print("shots ok")
