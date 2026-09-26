#!/usr/bin/env python3
import urllib.request, urllib.error, concurrent.futures, time, json
HOST='web-e7c4e657c650932c.web.h7tex.com'
BASE='http://'+HOST
base_words = '''
api v1 v2 docs documentation openapi swagger redoc health status ready metrics debug config env version robots.txt sitemap.xml
admin login register auth user users me dashboard home index app static assets js css favicon.ico
incident incidents incident-report incident_reports incidentreport report reports final final-report final_report finalreport atlas atlas-incident atlas_incident atlas/report atlas/final
case cases alert alerts issue issues ticket tickets event events investigation investigations intelligence intel research researcher research-assistant analyst analysis analyze triage review assess assessment evaluate evaluator adjudicate adjudication verdict decision decide confidence convince convinced escalation escalate escalations evidence evidences source sources article articles finding findings claim claims corroborate corroboration verify verification ingestion ingest submit url urls feed feeds memory state session sessions conversation conversations message messages chat ask query prompt prompts completion completions complete generate respond responses response run invoke infer predict classify model models llm agent agents bot webhook callback flag secret
open current active pending queue queues draft drafts finalise finalize issue-report publish published
'''.split()
phrases = [
'open-incident','open_incident','current-incident','current_incident','active-incident','active_incident','incident/open','incidents/open','incident/current','incidents/current','incident/active','incidents/active',
'final/report','report/final','reports/final','final-report','final_report','report/final-report','report/final_report','incidents/report','incident/report','incidents/final','incident/final',
'atlas/chat','atlas/ask','atlas/query','atlas/report','atlas/final','atlas/incident','atlas/evidence','atlas/research','atlas/analyze','atlas/escalate','atlas/final-report',
'api/incident/open','api/incidents/open','api/incident/current','api/incidents/current','api/report/final','api/reports/final','api/final/report','api/final-report','api/final_report','api/atlas/report','api/atlas/final','api/atlas/chat','api/atlas/ask','api/evidence/submit','api/incident/evidence','api/incidents/evidence',
'v1/incident/open','v1/incidents/open','v1/report/final','v1/final-report','api/v1/incident/open','api/v1/incidents/open','api/v1/report/final','api/v1/final-report',
'chat/completions','v1/chat/completions','api/chat/completions','api/v1/chat/completions','responses','v1/responses','api/responses','api/v1/responses',
'api/triage','api/analyze','api/review','api/assess','api/evaluate','api/adjudicate','api/verdict','api/decision','api/convince','api/escalate','api/finalize','api/publish'
]
paths=set('/'+w for w in base_words) | set('/'+p for p in phrases)
for prefix in ['', '/api', '/v1', '/api/v1']:
    for w in base_words:
        paths.add(prefix+'/'+w)
        paths.add(prefix+'/'+w+'/')
        if '.' not in w: paths.add(prefix+'/'+w+'.json')
# numeric/object guesses
for root in ['incident','incidents','case','cases','report','reports','api/incident','api/incidents','api/case','api/cases','api/report','api/reports']:
    for ident in ['1','0','open','current','active','INC-1','INC-001','atlas','echo','echo-chamber','echo_chamber']:
        paths.add('/'+root+'/'+ident)
        paths.add('/'+root+'/'+ident+'/report')
        paths.add('/'+root+'/'+ident+'/final')
        paths.add('/'+root+'/'+ident+'/evidence')

def fetch(path, method='GET'):
    data=None; headers={'User-Agent':'relay','Accept':'*/*'}
    if method=='POST':
        data=json.dumps({'message':'hello','prompt':'hello','text':'hello','query':'hello'}).encode(); headers['Content-Type']='application/json'
    req=urllib.request.Request(BASE+path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=4) as r:
            body=r.read(300)
            return method,path,r.status,dict(r.headers),body
    except urllib.error.HTTPError as e:
        body=e.read(300)
        return method,path,e.code,dict(e.headers),body
    except Exception as e:
        return method,path,'ERR',{},repr(e).encode()

def interesting(res):
    m,p,st,h,b=res; txt=b.decode('utf-8','replace')
    if st=='ERR': return False
    return not (st==404 and txt=='404 page not found\n')

print('FAST FUZZ', BASE, 'paths', len(paths))
start=time.time(); hits=[]
work=[]
for p in sorted(paths): work.append(('GET',p)); work.append(('POST',p))
with concurrent.futures.ThreadPoolExecutor(max_workers=80) as ex:
    futs=[ex.submit(fetch,p,m) for m,p in work]
    for fut in concurrent.futures.as_completed(futs):
        r=fut.result()
        if interesting(r):
            hits.append(r)
            m,p,st,h,b=r
            print('HIT',m,p,'STATUS',st,'LEN',len(b),'CT',h.get('Content-Type'))
            print(b.decode('utf-8','replace')[:500].replace('\r',''))
print('hits',len(hits),'elapsed',time.time()-start)
print('done')
