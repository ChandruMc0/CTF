#!/usr/bin/env python3
import socket, ssl, sys, time
HOST='web-e7c4e657c650932c.web.h7tex.com'
ports=[80,443,8000,8080,3000,5000,5001,8081,8888,9000,9090,11434,7860,5173,8501,4000,7000,2375,1337,10000,10001]
print('PORT SCAN', HOST)
for p in ports:
    try:
        raw=socket.socket(); raw.settimeout(2); raw.connect((HOST,p))
        if p==443:
            try:
                s=ssl._create_unverified_context().wrap_socket(raw, server_hostname=HOST)
            except Exception as e:
                print('PORT',p,'TLSERR',repr(e)); raw.close(); continue
        else:
            s=raw
        s.settimeout(2)
        s.sendall(f'GET / HTTP/1.1\r\nHost: {HOST}\r\nUser-Agent: relay\r\nConnection: close\r\n\r\n'.encode())
        data=b''
        try:
            while len(data)<1024:
                chunk=s.recv(1024)
                if not chunk: break
                data+=chunk
        except Exception as e:
            pass
        print('PORT',p,'RESP',repr(data[:1000]))
        s.close()
    except Exception as e:
        print('PORT',p,'ERR',type(e).__name__,str(e)[:200])
print('done')
