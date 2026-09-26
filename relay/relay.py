#!/usr/bin/env python3
import urllib.request, urllib.parse, urllib.error, json, socket, ssl, time, sys, itertools
HOST='web-e7c4e657c650932c.web.h7tex.com'
BASE='http://'+HOST

def req(method,path,body=None,headers=None,timeout=8, base=BASE):
    url=base+path
    data=None
    hs={'User-Agent':'Mozilla/5.0 relay'}
    if headers: hs.update(headers)
    if body is not None:
        if isinstance(body,(dict,list)):
            data=json.dumps(body).encode(); hs.setdefault('Content-Type','application/json')
        elif isinstance(body,str):
            data=body.encode()
        else:
            data=body
    r=urllib.request.Request(url, data=data, headers=hs, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            b=resp.read(4096)
            return resp.status, dict(resp.headers), b
    except urllib.error.HTTPError as e:
        b=e.read(4096)
        return e.code, dict(e.headers), b
    except Exception as e:
        return 'ERR', {}, repr(e).encode()

def pr(label, st,h,b, force=False):
    txt=b.decode('utf-8','replace')
    interesting = force or st not in (404,) or ('404 page not found' not in txt)
    if interesting:
        print(f'### {label} STATUS={st} LEN={len(b)}')
        print('HEADERS', {k:v for k,v in h.items() if k.lower() in ['server','date','content-type','content-length','allow','location','access-control-allow-origin','access-control-allow-methods','x-powered-by']})
        print(txt[:2000].replace('\r',''))
        print('---')

print('BASE',BASE)
print('=== basic methods root ===')
for m in ['GET','HEAD','POST','OPTIONS','PUT','PATCH','DELETE']:
    st,h,b=req(m,'/',{} if m in ['POST','PUT','PATCH'] else None,timeout=10)
    pr(m+' /',st,h,b,force=True)

print('=== host/IP variants ===')
for base in ['http://'+HOST, 'http://34.93.46.24']:
    for hp in [None, HOST, 'localhost', '127.0.0.1', 'atlas', 'atlas.local']:
        hs={} if hp is None else {'Host':hp}
        st,h,b=req('GET','/',headers=hs,base=base,timeout=5)
        pr(f'GET {base}/ Host={hp}',st,h,b,force=True)

print('=== port scan http-ish ===')
ports=[80,443,8080,8000,3000,5000,5001,8081,8888,9000,9090,11434,7860,5173,8501,4000,7000,2375,1337,8008,8010,8880,9001,10000]
for p in ports:
    try:
        if p==443:
            context=ssl._create_unverified_context(); s=context.wrap_socket(socket.socket(),server_hostname=HOST)
        else:
            s=socket.socket()
        s.settimeout(3); s.connect((HOST,p))
        reqb=f'GET / HTTP/1.1\r\nHost: {HOST}\r\nConnection: close\r\nUser-Agent: relay\r\n\r\n'.encode()
        s.sendall(reqb)
        data=s.recv(200)
        print('PORT',p,'OPEN RESP',repr(data[:200]))
        s.close()
    except Exception as e:
        print('PORT',p,'ERR',repr(e))

words = '''
api v1 v2 status health ready live metrics docs swagger openapi.json swagger.json redoc index index.html home app ui admin login auth me whoami version debug vars config env info robots.txt sitemap.xml
chat chats ask query message messages prompt prompts complete completion completions generate generation respond response run invoke infer inference predict classify classification analyze analysis analyst assess assessment evaluate evaluation triage judge adjudicate review verdict decision decide confidence convince escalate escalation close finalize final final-report final_report report reports report-final finalreport issue issues incident incidents case cases open active current ticket tickets alert alerts event events finding findings evidence evidences source sources article articles url urls ingest ingestion submit submission add create update feed feeds research researcher intelligence atlas agent agents bot llm model models session sessions conversation conversations transcript memory state flag flag.txt secret proof claim claims verify verification corroborate corroboration
api/chat api/ask api/query api/message api/prompt api/generate api/respond api/run api/invoke api/analyze api/assess api/evaluate api/review api/verdict api/decision api/convince api/escalate api/finalize api/report api/reports api/final api/final-report api/final_report api/incident api/incidents api/case api/cases api/evidence api/source api/sources api/ingest api/submit api/research api/intelligence api/atlas api/agent api/session api/conversation api/state api/flag
v1/chat v1/ask v1/query v1/message v1/prompt v1/generate v1/respond v1/run v1/invoke v1/analyze v1/assess v1/evaluate v1/review v1/verdict v1/decision v1/convince v1/escalate v1/finalize v1/report v1/reports v1/final v1/incident v1/incidents v1/evidence v1/submit
api/v1/chat api/v1/ask api/v1/query api/v1/message api/v1/prompt api/v1/generate api/v1/respond api/v1/run api/v1/invoke api/v1/analyze api/v1/assess api/v1/evaluate api/v1/review api/v1/verdict api/v1/decision api/v1/convince api/v1/escalate api/v1/finalize api/v1/report api/v1/reports api/v1/final api/v1/incident api/v1/incidents api/v1/evidence api/v1/submit
incident/open incidents/open incident/current incidents/current incident/active incidents/active incident/1 incidents/1 case/open cases/open case/current report/final reports/final report/1 reports/1 final/report open/incident open-case open-incident open_incident current-incident current_incident active-incident active_incident
atlas/chat atlas/ask atlas/query atlas/report atlas/final atlas/incident atlas/evidence atlas/research
chat/completions api/chat/completions completions/create responses api/responses v1/responses api/v1/responses
'''.split()
paths=[]
for w in words:
    if not w.startswith('/'): paths.append('/'+w)
# extensions and trailing slash variants for selected
more=[]
for p in paths:
    more.append(p); more.append(p+'/')
    if p.count('/')<=1 and not p.endswith('.json') and not p.endswith('.txt'):
        more.append(p+'.json')
paths=[]
seen=set()
for p in more:
    if p not in seen:
        seen.add(p); paths.append(p)
print('=== wordlist probes', len(paths),'===')
post_body={'message':'hello','prompt':'hello','query':'hello','input':'hello','text':'hello','url':'https://www.securityweek.com/new-echo-chamber-jailbreak-bypasses-ai-guardrails-with-ease/','evidence':'hello'}
for p in paths:
    st,h,b=req('GET',p,timeout=5); pr('GET '+p,st,h,b)
    # try POST for all word paths; if route exists but requires body/method should differ
    st,h,b=req('POST',p,post_body,timeout=8); pr('POST '+p,st,h,b)

print('done')
