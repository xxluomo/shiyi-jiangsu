"""通过本机随机控制令牌停止拾遗江苏，不操作其他项目。"""
import json
from pathlib import Path
import time
import urllib.request

ROOT=Path(__file__).resolve().parent
URL='http://127.0.0.1:8000'


def main():
    path=ROOT/'data/local-server.json'
    if not path.exists():print('No launcher record was found. Close the terminal if started manually.');return
    info=json.loads(path.read_text(encoding='utf-8'))
    try:
        with urllib.request.urlopen(URL+'/api/health',timeout=2) as response:health=json.load(response)
    except OSError:print('The museum is already stopped.');return
    if health.get('project')!='shiyi-jiangsu':raise SystemExit('This port belongs to another project. Nothing was stopped.')
    request=urllib.request.Request(URL+'/api/local-shutdown',data=b'{}',method='POST',
        headers={'Content-Type':'application/json','X-Local-Shutdown':info['token']})
    with urllib.request.urlopen(request,timeout=3) as response:json.load(response)
    for _ in range(30):
        time.sleep(.1)
        try:urllib.request.urlopen(URL+'/api/health',timeout=.5).close()
        except OSError:print('SHIYI JIANGSU stopped.');return
    raise SystemExit('Shutdown is still in progress.')


if __name__=='__main__':main()
