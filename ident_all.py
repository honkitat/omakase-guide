import json, urllib.request, base64, io, time, re, os
from PIL import Image
BASE="/opt/data/omakase-guide"; D="/opt/data/cache/images"
env={}
for line in open("/opt/data/.env",encoding="utf-8",errors="ignore"):
    line=line.strip()
    if line and not line.startswith("#") and "=" in line:
        k,v=line.split("=",1); env[k.strip()]=v.strip().strip('"').strip("'")
KEY=env.get("PRYSM_API_KEY","")
imgs=json.load(open(f"{BASE}/new_imgs.json",encoding="utf-8"))
fish=json.load(open(f"{BASE}/fish.json",encoding="utf-8"))
names=[f["j"] for f in fish]
try:
    res=json.load(open(f"{BASE}/ident_results.json",encoding="utf-8"))
except Exception:
    res={}

def b64(p):
    im=Image.open(p).convert("RGB"); im.thumbnail((600,600))
    b=io.BytesIO(); im.save(b,"JPEG",quality=70)
    return base64.b64encode(b.getvalue()).decode()

SYS=("你是頂級寿司店板前。逐張相辨認壽司ネタ（topping），要精準。\n"
     "只能從以下既有魚種清單中選一個（用完全相同的字串）；若明顯唔屬於清單，jp 填 \"OTHER\"。\n"
     "清單：" + "、".join(names) + "\n\n"
     "每張輸出一個 JSON object："
     "{\"id\":\"IMG_n\",\"jp\":\"清單中嘅魚名或OTHER\",\"confidence\":0-100,"
     "\"evidence\":\"關鍵視覺證據（顏色/魚皮/刀紋/醬汁/切法）\",\"not_fish\":false}\n"
     "只輸出 JSON array，不要其他文字。")

def call(batch):
    content=[{"type":"text","text":f"辨認以下 {len(batch)} 張相。"}]
    for i,n in enumerate(batch):
        content.append({"type":"text","text":f"IMG_{i+1} = {n}"})
        content.append({"type":"image_url","image_url":{"url":"data:image/jpeg;base64,"+b64(f"{D}/{n}")}})
    body=json.dumps({"model":"claude-opus-5","messages":[
        {"role":"system","content":SYS},{"role":"user","content":content}],"max_tokens":4000}).encode()
    req=urllib.request.Request("https://www.prysmapi.cn/v1/chat/completions", data=body,
        headers={"Authorization":f"Bearer {KEY}","Content-Type":"application/json"})
    r=json.loads(urllib.request.urlopen(req,timeout=300).read())
    return r["choices"][0]["message"].get("content") or ""

todo=[n for n in imgs if n not in res]
print("todo",len(todo), flush=True)
B=8
for s in range(0,len(todo),B):
    batch=todo[s:s+B]
    for attempt in range(3):
        try:
            txt=call(batch)
            arr=json.loads(re.search(r'\[[\s\S]*\]',txt).group(0))
            got=0
            for o in arr:
                m=re.match(r'IMG_(\d+)', str(o.get("id","")))
                if not m: continue
                idx=int(m.group(1))-1
                if 0<=idx<len(batch):
                    o["file"]=batch[idx]; res[batch[idx]]=o; got+=1
            print(f"batch {s//B}: {got}/{len(batch)} (total {len(res)})", flush=True)
            break
        except Exception as e:
            print("retry",s//B,type(e).__name__,str(e)[:90], flush=True); time.sleep(5)
    json.dump(res, open(f"{BASE}/ident_results.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
    time.sleep(1)
print("DONE",len(res),"/",len(imgs), flush=True)
