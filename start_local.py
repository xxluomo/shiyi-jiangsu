"""本机启动器：检查服务就绪后打开浏览器；重复启动复用已有服务。"""
import argparse
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser

ROOT=Path(__file__).resolve().parent
URL='http://127.0.0.1:8000'
CONTROL=ROOT/'data/local-server.json'


def ready():
    try:
        with urllib.request.urlopen(URL+'/api/health',timeout=1) as response:
            data=json.load(response)
        return data.get('project')=='shiyi-jiangsu' and data.get('version')==2
    except Exception:return False


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--no-browser',action='store_true')
    args=parser.parse_args()
    if ready():
        print('The museum is already running: '+URL)
        if not args.no_browser:webbrowser.open(URL)
        return
    with socket.socket() as sock:
        if sock.connect_ex(('127.0.0.1',8000))==0:
            raise SystemExit('Port 8000 is in use. Close the previous server before starting this version.')
    token=secrets.token_urlsafe(32);env=os.environ.copy();env['SHIYI_STOP_TOKEN']=token;env['PYTHONIOENCODING']='utf-8'
    process=subprocess.Popen([sys.executable,str(ROOT/'server.py')],cwd=ROOT,env=env)
    CONTROL.parent.mkdir(parents=True,exist_ok=True)
    CONTROL.write_text(json.dumps({'pid':process.pid,'token':token}),encoding='utf-8')
    try:
        for _ in range(100):
            if process.poll() is not None:raise SystemExit('Server failed to start. Read the error above.')
            if ready():break
            time.sleep(.2)
        else:raise SystemExit('Startup timed out.')
        print('\nWebsite: '+URL+'\nDemo: student / 123456\nAdmin: admin / 123456\nKeep this window open. Ctrl+C stops the server.\n',flush=True)
        if not args.no_browser:webbrowser.open(URL)
        process.wait()
    except KeyboardInterrupt:pass
    finally:
        if process.poll() is None:process.terminate();process.wait(timeout=10)
        try:
            if json.loads(CONTROL.read_text(encoding='utf-8')).get('pid')==process.pid:CONTROL.unlink()
        except (FileNotFoundError,ValueError):pass


if __name__=='__main__':main()
