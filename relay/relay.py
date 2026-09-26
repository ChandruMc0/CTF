#!/usr/bin/env python3
import urllib.request, urllib.parse, urllib.error, json, time, sys
BASE='http://web-e7c4e657c650932c.web.h7tex.com'

def req(method,path,body=None,headers=None,timeout=20):
    url=BASE+path
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

def show(label, status, headers, body):
    text=body.decode('utf-8','replace')
    ct=headers.get('Content-Type','')
    interesting = status not in (404,) or ('404 page not found' not in text)
    # print compact for all non-GET post probes and interesting
    if interesting:
        print(f'### {label} STATUS={status} CT={ct} LEN={len(body)}')
        for k in ['Allow','Server','Location','Access-Control-Allow-Origin','Access-Control-Allow-Methods']:
            if k in headers: print(f'{k}: {headers[k]}')
        print(text[:2000].replace('\r',''))
        print('---')
    else:
        print(f'{label} -> 404')

paths = [
'/', '/health','/status','/ready','/live','/metrics','/version','/debug','/debug/vars','/docs','/openapi.json','/swagger.json','/swagger/index.html',
'/api','/api/health','/api/status','/api/docs','/api/openapi.json',
'/chat','/ask','/query','/message','/prompt','/complete','/completion','/generate','/respond','/run','/infer','/predict',
'/api/chat','/api/ask','/api/query','/api/message','/api/prompt','/api/complete','/api/completion','/api/generate','/api/respond','/api/run','/api/infer','/api/predict',
'/v1/chat','/v1/ask','/v1/query','/v1/completions','/v1/chat/completions','/v1/models','/api/v1/chat','/api/v1/ask','/api/v1/query','/api/v1/completions','/api/v1/chat/completions',
'/incident','/incidents','/case','/cases','/open','/evidence','/submit','/analyze','/analysis','/escalate','/convince','/report','/reports','/final','/final-report',
'/api/incident','/api/incidents','/api/case','/api/cases','/api/open','/api/evidence','/api/submit','/api/analyze','/api/analysis','/api/escalate','/api/convince','/api/report','/api/reports','/api/final','/api/final-report',
'/incident/open','/incidents/open','/case/open','/cases/open','/report/final','/reports/final','/api/incident/open','/api/incidents/open','/api/case/open','/api/cases/open','/api/report/final','/api/reports/final',
'/session','/sessions','/api/session','/api/sessions','/conversation','/conversations','/api/conversation','/api/conversations',
'/agent','/agents','/atlas','/api/atlas','/atlas/chat','/atlas/ask','/atlas/report'
]
print('BASE',BASE)
print('--- GET/OPTIONS discovery ---')
for p in paths:
    st,h,b=req('GET',p,timeout=8); show('GET '+p,st,h,b)
    if st!=404:
        pass
print('--- POST discovery ---')
payloads=[
 {'message':'hello'},
 {'prompt':'hello'},
 {'query':'hello'},
 {'input':'hello'},
 {'text':'hello'},
 {'url':'https://www.securityweek.com/new-echo-chamber-jailbreak-bypasses-ai-guardrails-with-ease/'},
 {'evidence':'hello'},
]
for p in paths:
    # only likely interactive/API paths
    if not any(s in p for s in ['chat','ask','query','message','prompt','complete','generate','respond','run','infer','predict','incident','case','evidence','submit','analy','escalate','convince','report','final','atlas','session','conversation']) and p not in ['/','/api']:
        continue
    for body in payloads[:1]:
        st,h,b=req('POST',p,body,timeout=12)
        txt=b.decode('utf-8','replace')
        if st!=404 or '404 page not found' not in txt:
            show('POST '+p+' '+json.dumps(body),st,h,b)
            break
print('done')
