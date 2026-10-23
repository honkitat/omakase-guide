import json, urllib.request, time, re, os
BASE="/opt/data/omakase-guide"
env={}
for line in open("/opt/data/.env",encoding="utf-8",errors="ignore"):
    line=line.strip()
    if line and not line.startswith("#") and "=" in line:
        k,v=line.split("=",1); env[k.strip()]=v.strip().strip('"').strip("'")
KEY=env.get("DEEPSEEK_API_KEY","")
fish=json.load(open(f"{BASE}/fish.json",encoding="utf-8"))
try:
    new=json.load(open(f"{BASE}/descriptions.json",encoding="utf-8"))
except Exception:
    new={}

SYS="""你係一位深諳日本料理文化嘅中文作家，文字典雅、克制、有畫面感。
請為每個魚種寫一段繁體中文介紹（香港書面語，65–95字）：
- 用語優雅，絕不使用廣東話口語（「嘅／咗／啲／唔」一律不可以出現）。
- 必須包含一個該魚嘅特別故事或冷知識：名稱由來、產地、歷史、職人技法、季節典故或食俗。
- 避免堆砌形容詞，避免每段同一句式。
輸出 JSON array，每個元素只含兩個欄位：{"j":"魚名","d":"介紹"}。不要輸出其他文字。"""

def call(items):
    body=json.dumps({"model":"deepseek-flash","messages":[
        {"role":"system","content":SYS},
        {"role":"user","content":json.dumps(items,ensure_ascii=False)}],
        "max_tokens":8000,"temperature":0.85}).encode()
    req=urllib.request.Request("https://api.deepseek.com/chat/completions", data=body,
        headers={"Authorization":f"Bearer {KEY}","Content-Type":"application/json"})
    r=json.loads(urllib.request.urlopen(req,timeout=600).read())
    return r["choices"][0]["message"].get("content") or ""

todo=[f for f in fish if f["j"] not in new]
print("todo:", len(todo), flush=True)
B=12
for s in range(0,len(todo),B):
    batch=todo[s:s+B]
    items=[{"j":f["j"],"zh":f.get("zh",""),"en":f.get("en",""),"season":f.get("m",[]),
            "taste":f.get("f",""),"texture":f.get("t",""),"prep":f.get("prep",[]),"old":f.get("d","")} for f in batch]
    got=0
    for attempt in range(4):
        try:
            txt=call(items)
            m=re.search(r'\[[\s\S]*\]', txt)
            arr=json.loads(m.group(0))
            for o in arr:
                j=o.get("j"); d=o.get("d") or o.get("description") or o.get("intro") or o.get("text")
                if j and d: new[j]=d.strip(); got+=1
            print(f"batch {s//B}: {got}/{len(batch)} (total {len(new)})", flush=True)
            break
        except Exception as e:
            print("retry",s//B,type(e).__name__,str(e)[:100], flush=True); time.sleep(5)
    json.dump(new, open(f"{BASE}/descriptions.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
    time.sleep(1)
print("DONE total:",len(new),"/",len(fish), flush=True)
