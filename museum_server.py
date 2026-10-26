"""拾遗江苏：本地HTTP服务、用户权限、媒体处理与学习业务。"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.cookies import SimpleCookie
from urllib.parse import urlparse, parse_qs, unquote
from pathlib import Path
from io import BytesIO
import argparse
import base64
import hashlib
import hmac
import json
import mimetypes
import os
import re
import secrets
import threading
import time
import wave
from PIL import Image, ImageOps, UnidentifiedImageError
import museum_db as db

Image.MAX_IMAGE_PIXELS = 20_000_000
MAX_BODY = 12*1024*1024


class Error(Exception):
    def __init__(self,status,message): self.status,self.message=status,message


def text(body,key,limit=200,required=True):
    value=body.get(key,'')
    if not isinstance(value,str) or len(value.strip())>limit or (required and not value.strip()):
        raise Error(400,f'{key}请填写有效内容（最多{limit}字）')
    return value.strip()


def item_values(body):
    result={key:text(body,key,limit) for key,limit in [('title',80),('category',20),('region',80),('city',20),
      ('theme',20),('summary',300),('content',16000),('source_url',700),('source_name',160),('image',250)]}
    if result['category'] not in db.CATEGORIES or result['theme'] not in db.THEMES or result['city'] not in db.CITIES:
        raise Error(400,'请选择有效的城市、类别和专题')
    source=urlparse(result['source_url'])
    if source.scheme not in ['https','http'] or not source.netloc: raise Error(400,'来源网址必须以http或https开头')
    result['material']=text(body,'material',100,False)
    result['slug']=text(body,'slug',80,False) or 'item-'+secrets.token_hex(6)
    if type(body.get('published',True)) is not bool: raise Error(400,'发布状态无效')
    result['published']=int(body.get('published',True))
    for key,minimum,maximum in [('steps',1,10),('tags',0,8),('gallery',0,6)]:
        values=body.get(key,[])
        if not isinstance(values,list) or not minimum<=len(values)<=maximum or any(not isinstance(s,str) or not s.strip() or len(s)>400 for s in values):
            raise Error(400,f'{key}格式错误')
        result[key]=values
    for image in [result['image'],*result['gallery']]:
        if not image.startswith(('/assets/','/uploads/')) or '..' in image or '?' in image or '#' in image:
            raise Error(400,'请选择本地配图或上传图片')
        base=db.ROOT/'static' if image.startswith('/assets/') else db.DATA
        path=(base/image.lstrip('/')).resolve()
        if not path.is_relative_to(base.resolve()) or not path.is_file(): raise Error(400,'配图文件不存在')
    for key in ['steps','tags','gallery']: result[key]=json.dumps(result[key],ensure_ascii=False)
    return result


def question_values(body):
    prompt=text(body,'prompt',500)
    options=body.get('options')
    answer=body.get('answer')
    if not isinstance(options,list) or len(options)!=4 or any(not isinstance(s,str) or not s.strip() or len(s)>200 for s in options):
        raise Error(400,'请填写四个有效选项')
    if type(answer) is not int or answer not in range(4): raise Error(400,'请选择正确答案')
    return (prompt,json.dumps([s.strip() for s in options],ensure_ascii=False),answer,
            text(body,'explanation',1500),text(body,'topic',40,False) or '综合知识')


def save_image(encoded):
    if not isinstance(encoded,str): raise Error(400,'图片格式错误')
    try: binary=base64.b64decode(encoded,validate=True)
    except (ValueError,TypeError): raise Error(400,'图片编码无效')
    if not 0<len(binary)<=8*1024*1024: raise Error(413,'图片不能超过8MB')
    try:
        with Image.open(BytesIO(binary)) as original:
            if original.format not in ['PNG','JPEG','WEBP','GIF']: raise Error(400,'仅支持PNG、JPEG、WebP或GIF图片')
            original.load()
            image=ImageOps.exif_transpose(original).convert('RGB')
            if image.width<1 or image.height<1: raise Error(400,'无效图片尺寸')
            image.thumbnail((2200,2200))
            name=secrets.token_hex(16)
            image.save(db.UPLOADS/(name+'.webp'),'WEBP',quality=88)
            image.thumbnail((560,560))
            image.save(db.UPLOADS/(name+'-thumb.webp'),'WEBP',quality=80)
    except (UnidentifiedImageError,OSError,ValueError,Image.DecompressionBombError,Image.DecompressionBombWarning):
        raise Error(400,'图片损坏、尺寸过大或无法解码')
    return {'url':'/uploads/'+name+'.webp','thumb':'/uploads/'+name+'-thumb.webp'}


class Handler(BaseHTTPRequestHandler):
    server_version='ShiyiJiangsu/2.0'
    def log_message(self,*args): pass
    def security(self):
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('X-Frame-Options','DENY')
        self.send_header('Referrer-Policy','strict-origin-when-cross-origin')
        self.send_header('Content-Security-Policy',"default-src 'self'; img-src 'self' data: blob:; media-src 'self' blob:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'")
    def respond(self,status,payload,headers=None):
        binary=json.dumps(payload,ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(binary)))
        self.send_header('Cache-Control','no-store')
        self.security()
        for key,value in (headers or {}).items(): self.send_header(key,value)
        self.end_headers()
        if self.command!='HEAD': self.wfile.write(binary)
    def body(self):
        try: size=int(self.headers.get('Content-Length','0'))
        except ValueError: raise Error(400,'请求长度无效')
        if not 0<size<=MAX_BODY: raise Error(413,'提交内容为空或过大')
        if self.headers.get_content_type()!='application/json': raise Error(415,'请提交JSON数据')
        try: data=json.loads(self.rfile.read(size))
        except (ValueError,UnicodeError): raise Error(400,'JSON格式无效')
        if not isinstance(data,dict): raise Error(400,'请求内容必须是对象')
        return data
    def user(self,required=False,admin=False):
        cookies=SimpleCookie()
        try: cookies.load(self.headers.get('Cookie',''))
        except Exception: pass
        token=cookies.get('shiyi_session')
        digest=hashlib.sha256(token.value.encode()).hexdigest() if token else ''
        with db.connect() as con:
            row=con.execute('SELECT u.id,u.username,u.nickname,u.role,s.csrf,s.token_hash FROM auth_sessions s '
              'JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND s.expires>?',(digest,time.time())).fetchone()
        if (required or admin) and not row: raise Error(401,'请先登录账号')
        if admin and row['role']!='admin': raise Error(403,'需要管理员权限')
        if (required or admin) and self.command in ['POST','PUT','DELETE']:
            if not hmac.compare_digest(self.headers.get('X-CSRF-Token',''),row['csrf']): raise Error(403,'登录校验失效，请重新登录')
        return row
    def signin(self,user):
        token,csrf=secrets.token_urlsafe(32),secrets.token_urlsafe(24)
        with db.connect() as con:
            con.execute('DELETE FROM auth_sessions WHERE expires<?',(time.time(),))
            con.execute('INSERT INTO auth_sessions VALUES(?,?,?,?)',
                (hashlib.sha256(token.encode()).hexdigest(),user['id'],csrf,time.time()+86400))
        return self.respond(200,{'user':{k:user[k] for k in ['id','username','nickname','role']},'csrf':csrf},
          {'Set-Cookie':f'shiyi_session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=86400'})

    def route(self):
        parsed=urlparse(self.path); path=parsed.path; query=parse_qs(parsed.query); method=self.command
        q=lambda key,default='':query.get(key,[default])[0]
        if method in ['POST','PUT','DELETE']:
            origin=self.headers.get('Origin')
            if origin and urlparse(origin).netloc!=self.headers.get('Host'): raise Error(403,'不允许跨站提交')
        if path=='/api/health' and method=='GET':
            with db.connect() as con: con.execute('SELECT 1')
            return self.respond(200,{'ok':True,'project':'shiyi-jiangsu','version':2,'database':'SQLite'})
        if path=='/api/local-shutdown' and method=='POST':
            expected=os.environ.get('SHIYI_STOP_TOKEN','')
            if not expected or not hmac.compare_digest(expected,self.headers.get('X-Local-Shutdown','')): raise Error(403,'无权停止服务')
            threading.Timer(.5,self.server.shutdown).start()
            return self.respond(200,{'ok':True})
        if path=='/api/session' and method=='GET':
            user=self.user()
            return self.respond(200,{'user':{k:user[k] for k in ['id','username','nickname','role']} if user else None,'csrf':user['csrf'] if user else ''})
        if path in ['/api/login','/api/register'] and method=='POST':
            body=self.body(); username=text(body,'username',24); password=text(body,'password',128)
            if not re.fullmatch(r'[a-zA-Z0-9_]{3,24}',username): raise Error(400,'账号需为3—24位字母、数字或下划线')
            if not 6<=len(password)<=128: raise Error(400,'密码至少6位')
            now=time.time()
            with self.server.rate_lock:
                self.server.attempts=[t for t in self.server.attempts if t>now-60]
                if len(self.server.attempts)>=25: raise Error(429,'操作过于频繁，请一分钟后再试')
                self.server.attempts.append(now)
            with db.connect() as con:
                if path.endswith('register'):
                    if con.execute('SELECT 1 FROM users WHERE username=?',(username,)).fetchone(): raise Error(409,'这个账号已被注册')
                    salt=secrets.token_hex(16)
                    con.execute('INSERT INTO users(username,nickname,salt,password_hash) VALUES(?,?,?,?)',
                      (username,text(body,'nickname',30,False) or username,salt,db.hashed(password,salt)))
                user=con.execute('SELECT * FROM users WHERE username=?',(username,)).fetchone()
                candidate=db.hashed(password,user['salt'] if user else 'invalid')
                if not user or not hmac.compare_digest(user['password_hash'],candidate): raise Error(401,'账号或密码不正确')
            return self.signin(user)
        if path=='/api/logout' and method=='POST':
            user=self.user(True)
            with db.connect() as con: con.execute('DELETE FROM auth_sessions WHERE token_hash=?',(user['token_hash'],))
            return self.respond(200,{'ok':True},{'Set-Cookie':'shiyi_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0'})
        if path=='/api/catalog' and method=='GET':
            with db.connect() as con:
                rows=con.execute('SELECT * FROM items WHERE published=1 ORDER BY id').fetchall()
                questions=con.execute('SELECT COUNT(*) FROM questions').fetchone()[0]
                guides=[dict(r) for r in con.execute('SELECT * FROM guides ORDER BY id')]
            items=[db.unpack_item(r) for r in rows]
            return self.respond(200,{'items':items,'cities':db.CITIES,'categories':db.CATEGORIES,'themes':db.THEMES,
              'guides':guides,'stats':{'items':len(items),'cities':len({i['city'] for i in items}),
              'questions':questions,'guides':len(guides)}})
        if path=='/api/items' and method=='GET':
            clauses,args=[],[]
            if q('all')=='1': self.user(admin=True)
            else: clauses.append('published=1')
            if q('q'):
                clauses.append('(title LIKE ? OR content LIKE ? OR tags LIKE ?)');args.extend(['%'+q('q')[:100]+'%']*3)
            for field in ['city','category','theme']:
                if q(field): clauses.append(field+'=?');args.append(q(field))
            with db.connect() as con:
                rows=con.execute('SELECT * FROM items'+(' WHERE '+' AND '.join(clauses) if clauses else '')+' ORDER BY id',args).fetchall()
            return self.respond(200,{'items':[db.unpack_item(r) for r in rows]})
        match=re.fullmatch(r'/api/items/(\d+)',path)
        if match:
            ident=int(match[1])
            with db.connect() as con: row=con.execute('SELECT * FROM items WHERE id=?',(ident,)).fetchone()
            if not row: raise Error(404,'项目不存在或已被删除')
            if method=='GET':
                if not row['published']:
                    viewer=self.user()
                    if not viewer or viewer['role']!='admin': raise Error(404,'项目未发布')
                return self.respond(200,db.unpack_item(row))
            self.user(admin=True)
            if method=='DELETE':
                with db.connect() as con: con.execute('DELETE FROM items WHERE id=?',(ident,))
                return self.respond(200,{'ok':True})
            if method=='PUT':
                values=item_values(self.body())
                with db.connect() as con:
                    con.execute('UPDATE items SET '+','.join(k+'=:'+k for k in values)+',updated_at=CURRENT_TIMESTAMP WHERE id=:id',{**values,'id':ident})
                return self.respond(200,{'id':ident})
        if path=='/api/items' and method=='POST':
            self.user(admin=True); values=item_values(self.body())
            with db.connect() as con:
                cursor=con.execute('INSERT INTO items('+','.join(values)+') VALUES('+','.join(':'+k for k in values)+')',values)
                ident=cursor.lastrowid
            return self.respond(201,{'id':ident})
        if path=='/api/upload' and method=='POST':
            self.user(admin=True)
            return self.respond(201,save_image(self.body().get('data')))
        if path=='/api/export' and method=='POST':
            try:
                binary=base64.b64decode(self.body().get('data',''),validate=True)
                if not 0<len(binary)<=8*1024*1024: raise Error(413,'导出内容过大')
                with Image.open(BytesIO(binary)) as image:
                    if image.format!='PNG' or image.size!=(720,720): raise Error(400,'请导出720像素的工坊画布')
                    image.load();name='export-'+secrets.token_hex(16)+'.png'
                    image.save(db.UPLOADS/name,'PNG',optimize=True)
            except (ValueError,TypeError,UnidentifiedImageError,OSError,Image.DecompressionBombError):
                raise Error(400,'画布图像无效')
            return self.respond(201,{'url':'/uploads/'+name+'?download=1'})
        if path=='/api/admin/audio' and method=='POST':
            self.user(admin=True)
            try:
                binary=base64.b64decode(self.body().get('data',''),validate=True)
                if not 0<len(binary)<=8*1024*1024: raise Error(413,'音频不能超过8MB')
                with wave.open(BytesIO(binary),'rb') as audio:
                    if audio.getnchannels() not in [1,2] or audio.getnframes()/audio.getframerate()>180:
                        raise Error(400,'请上传3分钟内的单声道或双声道WAV音频')
            except (ValueError,TypeError,wave.Error,EOFError): raise Error(400,'WAV音频无效')
            name=secrets.token_hex(16)+'.wav';(db.UPLOADS/name).write_bytes(binary)
            return self.respond(201,{'url':'/uploads/'+name})
        if path=='/api/favorites' and method=='GET':
            user=self.user(True)
            with db.connect() as con:
                ids=[r[0] for r in con.execute('SELECT item_id FROM favorites WHERE user_id=?',(user['id'],))]
            return self.respond(200,{'ids':ids})
        match=re.fullmatch(r'/api/favorites/(\d+)',path)
        if match and method in ['POST','DELETE']:
            user=self.user(True); ident=int(match[1])
            with db.connect() as con:
                if not con.execute('SELECT 1 FROM items WHERE id=? AND published=1',(ident,)).fetchone(): raise Error(404,'项目不存在或未发布')
                if method=='POST': con.execute('INSERT OR IGNORE INTO favorites(user_id,item_id) VALUES(?,?)',(user['id'],ident))
                else: con.execute('DELETE FROM favorites WHERE user_id=? AND item_id=?',(user['id'],ident))
            return self.respond(200,{'ok':True})
        if path=='/api/progress' and method=='POST':
            user=self.user(True); body=self.body(); ident=body.get('item_id');step=body.get('step')
            if type(ident) is not int or type(step) is not int: raise Error(400,'学习进度格式无效')
            with db.connect() as con:
                row=con.execute('SELECT steps FROM items WHERE id=?',(ident,)).fetchone()
                if not row: raise Error(404,'项目不存在')
                count=len(json.loads(row['steps']))
                if not 0<=step<count: raise Error(400,'步骤无效')
                con.execute('INSERT INTO progress(user_id,item_id,step,completed) VALUES(?,?,?,?) '
                  'ON CONFLICT(user_id,item_id) DO UPDATE SET step=MAX(progress.step,excluded.step),'
                  'completed=MAX(progress.completed,excluded.completed),updated_at=CURRENT_TIMESTAMP',
                  (user['id'],ident,step,int(step==count-1)))
            return self.respond(200,{'ok':True})
        if path=='/api/works' and method=='POST':
            user=self.user(True); body=self.body(); kind=body.get('kind')
            if kind not in ['papercut','bluecloth']: raise Error(400,'创作类型无效')
            title=text(body,'title',60); params=body.get('params',{})
            if not isinstance(params,dict) or len(json.dumps(params))>150000: raise Error(400,'创作参数过大')
            image=save_image(body.get('data'))
            with db.connect() as con:
                cursor=con.execute('INSERT INTO works(user_id,title,kind,params,image,thumb) VALUES(?,?,?,?,?,?)',
                  (user['id'],title,kind,json.dumps(params,ensure_ascii=False),image['url'],image['thumb']))
                ident=cursor.lastrowid
            return self.respond(201,{'id':ident,**image})
        match=re.fullmatch(r'/api/works/(\d+)',path)
        if match and method=='DELETE':
            user=self.user(True)
            with db.connect() as con:
                cursor=con.execute('DELETE FROM works WHERE id=? AND user_id=?',(int(match[1]),user['id']))
                if not cursor.rowcount: raise Error(404,'作品不存在')
            return self.respond(200,{'ok':True})
        if path=='/api/me' and method=='GET':
            user=self.user(True)
            with db.connect() as con:
                favorites=[r[0] for r in con.execute('SELECT item_id FROM favorites WHERE user_id=?',(user['id'],))]
                progress=[dict(r) for r in con.execute('SELECT * FROM progress WHERE user_id=? ORDER BY updated_at DESC',(user['id'],))]
                attempts=[dict(r) for r in con.execute('SELECT * FROM attempts WHERE user_id=? ORDER BY id DESC LIMIT 30',(user['id'],))]
                works=[dict(r) for r in con.execute('SELECT id,title,kind,image,thumb,created_at FROM works WHERE user_id=? ORDER BY id DESC',(user['id'],))]
            for row in attempts: row['details']=json.loads(row['details'])
            return self.respond(200,{'favorites':favorites,'progress':progress,'attempts':attempts,'works':works})
        if path=='/api/quiz' and method=='GET':
            user=self.user()
            try: count=int(q('count','5'))
            except ValueError: raise Error(400,'题数无效')
            if count not in [5,10]: raise Error(400,'请选择5题或10题')
            with db.connect() as con:
                rows=con.execute('SELECT * FROM questions'+(' WHERE topic=?' if q('topic') else '')+' ORDER BY RANDOM() LIMIT ?',
                  (q('topic'),count) if q('topic') else (count,)).fetchall()
                if not rows: raise Error(400,'当前题库没有题目，请管理员先添加')
                ticket=secrets.token_urlsafe(24)
                con.execute('DELETE FROM quiz_tickets WHERE expires<?',(time.time(),))
                con.execute('INSERT INTO quiz_tickets(token,question_ids,expires,user_id,snapshot) VALUES(?,?,?,?,?)',
                  (ticket,json.dumps([r['id'] for r in rows]),time.time()+3600,user['id'] if user else None,
                   json.dumps([dict(r) for r in rows],ensure_ascii=False)))
            return self.respond(200,{'ticket':ticket,'questions':[{'id':r['id'],'prompt':r['prompt'],'options':json.loads(r['options'])} for r in rows]})
        if path=='/api/quiz/submit' and method=='POST':
            body=self.body(); ticket=text(body,'ticket',100);answers=body.get('answers');user=self.user()
            if not isinstance(answers,dict): raise Error(400,'答案格式错误')
            with db.connect() as con:
                con.execute('BEGIN IMMEDIATE')
                issued=con.execute('SELECT * FROM quiz_tickets WHERE token=? AND expires>?',(ticket,time.time())).fetchone()
                if not issued: raise Error(400,'本次答题已提交或过期，请重新开始')
                if issued['user_id'] and (not user or issued['user_id']!=user['id']): raise Error(403,'请使用开始答题时的账号提交')
                rows=json.loads(issued['snapshot'])
                if not rows: raise Error(400,'旧版题目已更新，请重新开始')
                results=[]
                for row in rows:
                    val=answers.get(str(row['id']));options=json.loads(row['options'])
                    if type(val) is not int or val not in range(4): raise Error(400,'请完成所有题目')
                    results.append({'id':row['id'],'prompt':row['prompt'],'selected':options[val],
                      'correct_text':options[row['answer']],'correct':val==row['answer'],'explanation':row['explanation']})
                correct=sum(r['correct'] for r in results);score=round(correct/len(rows)*100)
                con.execute('DELETE FROM quiz_tickets WHERE token=?',(ticket,))
                con.execute('INSERT INTO attempts(score,total,user_id,details) VALUES(?,?,?,?)',
                  (score,len(rows),issued['user_id'],json.dumps(results,ensure_ascii=False)))
            return self.respond(200,{'score':score,'correct':correct,'total':len(rows),'results':results})
        if path=='/api/admin/questions':
            self.user(admin=True)
            if method=='GET':
                with db.connect() as con: rows=[dict(r) for r in con.execute('SELECT * FROM questions ORDER BY id')]
                for row in rows: row['options']=json.loads(row['options'])
                return self.respond(200,{'questions':rows})
            if method=='POST':
                values=question_values(self.body())
                with db.connect() as con:
                    ident=con.execute('INSERT INTO questions(prompt,options,answer,explanation,topic) VALUES(?,?,?,?,?)',values).lastrowid
                return self.respond(201,{'id':ident})
        match=re.fullmatch(r'/api/admin/questions/(\d+)',path)
        if match and method in ['PUT','DELETE']:
            self.user(admin=True);ident=int(match[1])
            with db.connect() as con:
                if not con.execute('SELECT 1 FROM questions WHERE id=?',(ident,)).fetchone(): raise Error(404,'题目不存在')
                if method=='DELETE': con.execute('DELETE FROM questions WHERE id=?',(ident,))
                else: con.execute('UPDATE questions SET prompt=?,options=?,answer=?,explanation=?,topic=? WHERE id=?',(*question_values(self.body()),ident))
            return self.respond(200,{'ok':True})
        if path=='/api/admin/guides':
            self.user(admin=True)
            if method=='GET':
                with db.connect() as con: rows=[dict(r) for r in con.execute('SELECT * FROM guides')]
                return self.respond(200,{'guides':rows})
        match=re.fullmatch(r'/api/admin/guides/(\d+)',path)
        if match and method=='PUT':
            self.user(admin=True);body=self.body()
            with db.connect() as con:
                old=con.execute('SELECT * FROM guides WHERE id=?',(int(match[1]),)).fetchone()
                if not old: raise Error(404,'导览不存在')
                transcript=text(body,'text',5000);src=body.get('src',old['src'])
                if src!=old['src']:
                    if not isinstance(src,str) or not re.fullmatch(r'/uploads/[a-f0-9]{32}\.wav',src) or not (db.DATA/src.lstrip('/')).is_file():
                        raise Error(400,'请上传本地WAV音频')
                elif transcript!=old['text']: src=''
                con.execute('UPDATE guides SET title=?,text=?,src=? WHERE id=?',
                  (text(body,'title',100),transcript,src,int(match[1])))
            return self.respond(200,{'ok':True,'note':'导览已保存' if src else '文字稿已保存，音频待重新录制后上传'})
        if path=='/api/admin/stats' and method=='GET':
            self.user(admin=True)
            with db.connect() as con:
                counts={table:con.execute('SELECT COUNT(*) FROM '+table).fetchone()[0]
                    for table in ['items','questions','users','works','attempts','guides']}
                counts['average']=con.execute('SELECT COALESCE(ROUND(AVG(score),1),0) FROM attempts').fetchone()[0]
                counts['published']=con.execute('SELECT COUNT(*) FROM items WHERE published=1').fetchone()[0]
                counts['by_city']=[dict(r) for r in con.execute('SELECT city,COUNT(*) AS count FROM items WHERE published=1 GROUP BY city')]
                counts['recent']=[dict(r) for r in con.execute('SELECT a.id,a.score,a.total,a.created_at,COALESCE(u.nickname,\'访客\') AS nickname FROM attempts a LEFT JOIN users u ON a.user_id=u.id ORDER BY a.id DESC LIMIT 8')]
            return self.respond(200,counts)
        if path.startswith('/api/'): raise Error(404,'接口不存在或方法不支持')
        if method not in ['GET','HEAD']: raise Error(405,'请求方法不支持')
        self.file(path)

    def file(self,path):
        path=unquote(path)
        if path in ['/','/admin','/admin/']:
            target=db.ROOT/'static/index.html'
        elif path.startswith('/uploads/'):
            target=(db.DATA/path.lstrip('/')).resolve()
            if not target.is_relative_to(db.UPLOADS.resolve()): raise Error(404,'文件不存在')
        elif path.startswith(('/assets/','/audio/','/js/')) or path in ['/style.css','/site.css']:
            base=(db.ROOT/'static').resolve();target=(base/path.lstrip('/')).resolve()
            if not target.is_relative_to(base): raise Error(404,'文件不存在')
        else: raise Error(404,'页面不存在')
        if not target.is_file(): raise Error(404,'文件不存在')
        length=target.stat().st_size;start,end=0,length-1;status=200
        header=self.headers.get('Range','')
        match=re.fullmatch(r'bytes=(\d+)-(\d*)',header)
        if match:
            start=int(match[1]);end=min(int(match[2]) if match[2] else end,end)
            if start>end: raise Error(416,'无效范围')
            status=206
        self.send_response(status)
        mime=mimetypes.guess_type(target.name)[0] or 'application/octet-stream'
        self.send_header('Content-Type',mime+('; charset=utf-8' if mime.startswith('text/') else ''))
        self.send_header('Content-Length',str(end-start+1))
        self.send_header('Cache-Control','no-cache');self.send_header('Accept-Ranges','bytes')
        if target.name.startswith('export-') and parse_qs(urlparse(self.path).query).get('download')==['1']:
            self.send_header('Content-Disposition','attachment; filename="shiyi-design.png"')
        if status==206: self.send_header('Content-Range',f'bytes {start}-{end}/{length}')
        self.security();self.end_headers()
        if self.command!='HEAD':
            with target.open('rb') as file:
                file.seek(start); remaining=end-start+1
                while remaining:
                    chunk=file.read(min(65536,remaining))
                    if not chunk: break
                    self.wfile.write(chunk);remaining-=len(chunk)
    def dispatch(self):
        self.connection.settimeout(25)
        try:self.route()
        except Error as e:self.respond(e.status,{'error':e.message})
        except (BrokenPipeError,ConnectionResetError,TimeoutError):pass
        except Exception as e:
            print('Request error:',type(e).__name__,str(e),flush=True)
            self.respond(500,{'error':'服务器处理失败，请稍后重试'})
    do_GET=do_POST=do_PUT=do_DELETE=do_HEAD=dispatch


def create_server(port=8000):
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    server.rate_lock=threading.Lock();server.attempts=[]
    return server


def main():
    parser=argparse.ArgumentParser(description='拾遗江苏 · 非遗数字文化馆')
    parser.add_argument('--port',type=int,default=8000)
    parser.add_argument('--open',action='store_true')
    args=parser.parse_args();db.initialize();server=create_server(args.port)
    print(f'\nSHIYI JIANGSU: http://127.0.0.1:{args.port}\nLocal demo: admin / 123456; student / 123456\n',flush=True)
    if args.open:
        import webbrowser
        webbrowser.open(f'http://127.0.0.1:{args.port}')
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
