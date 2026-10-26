"""真实HTTP与临时SQLite集成验证；不改动交付数据库。"""
import base64
from io import BytesIO
import http.cookiejar
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import museum_db as db
import museum_server as app


class MuseumTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='shiyi-v2-')
        cls.original=(db.DATA,db.DB,db.UPLOADS)
        db.DATA=Path(cls.temp.name);db.DB=db.DATA/'test.db';db.UPLOADS=db.DATA/'uploads'
        db.initialize();cls.server=app.create_server(0)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.url=f'http://127.0.0.1:{cls.server.server_port}'
        cls.admin=cls.login('admin');cls.student=cls.login('student')
        output=BytesIO();Image.new('RGB',(40,30),'#b95040').save(output,'PNG')
        cls.png=output.getvalue();cls.encoded=base64.b64encode(cls.png).decode()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join()
        db.DATA,db.DB,db.UPLOADS=cls.original;cls.temp.cleanup()
    @classmethod
    def request(cls,path,method='GET',body=None,actor=None,headers=None,raw=None):
        head={'Content-Type':'application/json'}
        if actor:head['X-CSRF-Token']=actor.get('csrf','')
        head.update(headers or {})
        binary=raw if raw is not None else json.dumps(body).encode() if body is not None else None
        req=urllib.request.Request(cls.url+path,data=binary,headers=head,method=method)
        opener=actor['opener'] if actor else urllib.request.build_opener()
        try: response=opener.open(req,timeout=5)
        except urllib.error.HTTPError as error:response=error
        with response:
            payload=response.read()
            if 'application/json' in response.headers.get('Content-Type',''):payload=json.loads(payload)
            return response.status,payload,response.headers
    @classmethod
    def login(cls,name):
        actor={'opener':urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))}
        code,data,_=cls.request('/api/login','POST',{'username':name,'password':'123456'},actor)
        assert code==200,data
        actor['csrf']=data['csrf'];actor['id']=data['user']['id'];return actor
    def sample(self):
        return {'title':'测试馆藏','category':'传统美术','region':'江苏 · 南京','city':'南京','theme':'纸墨纹样',
          'summary':'测试简介','content':'原创整理说明。','steps':['观察：材料','创作：表达'],
          'image':'/assets/papercut.svg','source_url':'https://www.ihchina.cn/','source_name':'资料来源',
          'gallery':['/assets/papercut.svg','/assets/papercut-detail.svg'],'tags':['图案'],'material':'纸',
          'published':True}
    def test_01_catalog(self):
        code,data,_=self.request('/api/catalog');self.assertEqual(code,200)
        self.assertEqual(data['stats'],{'items':12,'cities':6,'questions':40,'guides':4})
        for i in data['items']:
            self.assertGreater(len(i['content']),300)
            self.assertGreaterEqual(len(i['gallery']),2)
    def test_02_all_assets_and_modules(self):
        catalog=self.request('/api/catalog')[1]
        paths=['/','/admin','/site.css','/assets/jiangsu-hero.png','/assets/jiangsu-cities.json']
        paths+=['/js/'+p.name for p in (db.ROOT/'static/js').glob('*.js')]
        paths+=list({url for i in catalog['items'] for url in [i['image'],*i['gallery']]})
        for path in paths:
            with self.subTest(path=path):self.assertEqual(self.request(path)[0],200)
    def test_03_audio_ranges(self):
        guides=self.request('/api/catalog')[1]['guides']
        for guide in guides:
            code,data,headers=self.request(guide['src'],headers={'Range':'bytes=0-43'})
            self.assertEqual(code,206);self.assertEqual(len(data),44);self.assertEqual(data[:4],b'RIFF')
            self.assertIn('bytes 0-43/',headers['Content-Range'])
    def test_04_login_and_session(self):
        data=self.request('/api/session',actor=self.student)[1]
        self.assertEqual(data['user']['username'],'student')
        self.assertEqual(self.request('/api/login','POST',{'username':'admin','password':'badbad'})[0],401)
    def test_05_registration(self):
        actor={'opener':urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))}
        code,data,_=self.request('/api/register','POST',{'username':'test_new','nickname':'新访客','password':'123456'},actor)
        self.assertEqual(code,200);self.assertEqual(data['user']['role'],'member')
        self.assertEqual(self.request('/api/register','POST',{'username':'test_new','password':'123456'})[0],409)
        self.assertEqual(self.request('/api/register','POST',{'username':'bad name','password':'123456'})[0],400)
    def test_06_permissions(self):
        self.assertEqual(self.request('/api/admin/stats')[0],401)
        self.assertEqual(self.request('/api/admin/stats',actor=self.student)[0],403)
        self.assertEqual(self.request('/api/items','POST',self.sample())[0],401)
        self.assertEqual(self.request('/api/items','POST',self.sample(),self.student)[0],403)
        self.assertEqual(self.request('/api/me')[0],401)
    def test_07_csrf_and_origin(self):
        self.assertEqual(self.request('/api/items','POST',self.sample(),self.admin,{'X-CSRF-Token':'bad'})[0],403)
        self.assertEqual(self.request('/api/items','POST',self.sample(),self.admin,{'Origin':'https://evil.example'})[0],403)
    def test_08_city_and_search(self):
        from urllib.parse import urlencode
        self.assertEqual(len(self.request('/api/items?'+urlencode({'city':'无锡'}))[1]['items']),4)
        self.assertEqual(len(self.request('/api/items?'+urlencode({'q':'云锦'}))[1]['items']),1)
        self.assertEqual(self.request('/api/items?q=NOTFOUND')[1]['items'],[])
        self.assertEqual(self.request('/api/items?q=%27%20OR%201%3D1--')[1]['items'],[])
    def test_09_item_crud_and_drafts(self):
        data=self.sample();data['published']=False
        code,created,_=self.request('/api/items','POST',data,self.admin);self.assertEqual(code,201)
        path='/api/items/'+str(created['id'])
        self.assertEqual(self.request(path)[0],404)
        self.assertEqual(self.request(path,actor=self.admin)[0],200)
        self.assertEqual(self.request('/api/items?all=1')[0],401)
        data['published']=True;data['title']='修改后的测试馆藏'
        self.assertEqual(self.request(path,'PUT',data,self.admin)[0],200)
        self.assertEqual(self.request(path)[1]['title'],data['title'])
        self.assertEqual(self.request(path,'DELETE',actor=self.admin)[0],200)
        self.assertEqual(self.request(path)[0],404)
    def test_10_validation(self):
        for patch in [{'title':''},{'city':'外省'},{'source_url':'javascript:alert(1)'},{'image':'/assets/../../server.py'},{'steps':[]},{'published':'yes'}]:
            self.assertEqual(self.request('/api/items','POST',{**self.sample(),**patch},self.admin)[0],400)
    def test_11_favorites(self):
        self.assertEqual(self.request('/api/favorites/1','POST',{},self.student)[0],200)
        self.request('/api/favorites/1','POST',{},self.student)
        self.assertEqual(self.request('/api/favorites',actor=self.student)[1]['ids'].count(1),1)
        self.assertNotIn(1,self.request('/api/favorites',actor=self.admin)[1]['ids'])
        self.assertEqual(self.request('/api/favorites/1','DELETE',actor=self.student)[0],200)
    def test_12_learning_progress(self):
        item=self.request('/api/items/1')[1]
        self.request('/api/progress','POST',{'item_id':1,'step':len(item['steps'])-1},self.student)
        self.request('/api/progress','POST',{'item_id':1,'step':0},self.student)
        row=self.request('/api/me',actor=self.student)[1]['progress'][0]
        self.assertTrue(row['completed']);self.assertEqual(row['step'],len(item['steps'])-1)
        self.assertEqual(self.request('/api/progress','POST',{'item_id':1,'step':999},self.student)[0],400)
    def test_13_upload_decode_thumbnail(self):
        code,data,_=self.request('/api/upload','POST',{'data':self.encoded},self.admin);self.assertEqual(code,201)
        for url in [data['url'],data['thumb']]:
            code,binary,_=self.request(url);self.assertEqual(code,200)
            with Image.open(BytesIO(binary)) as image:self.assertEqual(image.format,'WEBP')
        bad=base64.b64encode(b'\x89PNG\r\n\x1a\nNOT_IMAGE').decode()
        self.assertEqual(self.request('/api/upload','POST',{'data':bad},self.admin)[0],400)
    def test_14_works_ownership(self):
        code,data,_=self.request('/api/works','POST',{'title':'我的窗花','kind':'papercut','params':{'folds':8},'data':self.encoded},self.student)
        self.assertEqual(code,201)
        self.assertEqual(self.request('/api/works/'+str(data['id']),'DELETE',actor=self.admin)[0],404)
        self.assertTrue(any(w['id']==data['id'] for w in self.request('/api/me',actor=self.student)[1]['works']))
        self.assertEqual(self.request('/api/works/'+str(data['id']),'DELETE',actor=self.student)[0],200)
    def test_15_quiz_hidden_and_complete(self):
        quiz=self.request('/api/quiz')[1]
        self.assertEqual(len(quiz['questions']),5)
        self.assertNotIn('answer',quiz['questions'][0])
        self.assertEqual(self.request('/api/quiz/submit','POST',{'ticket':quiz['ticket'],'answers':{}})[0],400)
        self.assertEqual(self.request('/api/quiz?count=10')[1]['questions'].__len__(),10)
    def test_16_quiz_score_snapshot_replay(self):
        quiz=self.request('/api/quiz',actor=self.student)[1]
        with db.connect() as con:
            rows={q['id']:dict(con.execute('SELECT * FROM questions WHERE id=?',(q['id'],)).fetchone()) for q in quiz['questions']}
        answers={str(key):row['answer'] for key,row in rows.items()}
        first=next(iter(rows.values()));changed={**first,'options':json.loads(first['options']),'answer':(first['answer']+1)%4}
        self.request('/api/admin/questions/'+str(first['id']),'PUT',changed,self.admin)
        try:
            body={'ticket':quiz['ticket'],'answers':answers}
            self.assertEqual(self.request('/api/quiz/submit','POST',body,self.admin)[0],403)
            code,result,_=self.request('/api/quiz/submit','POST',body,self.student)
            self.assertEqual(code,200);self.assertEqual(result['score'],100)
            self.assertEqual(self.request('/api/quiz/submit','POST',body,self.student)[0],400)
            self.assertEqual(self.request('/api/me',actor=self.student)[1]['attempts'][0]['score'],100)
        finally:self.request('/api/admin/questions/'+str(first['id']),'PUT',{**first,'options':json.loads(first['options'])},self.admin)
    def test_17_question_crud(self):
        q={'prompt':'测试题？','options':['甲','乙','丙','丁'],'answer':0,'explanation':'示例解析','topic':'测试'}
        code,data,_=self.request('/api/admin/questions','POST',q,self.admin);self.assertEqual(code,201)
        path='/api/admin/questions/'+str(data['id']);q['answer']=2
        self.assertEqual(self.request(path,'PUT',q,self.admin)[0],200)
        self.assertEqual(self.request(path,'DELETE',actor=self.admin)[0],200)
        self.assertEqual(self.request('/api/admin/questions','POST',{**q,'answer':7},self.admin)[0],400)
    def test_18_guides_and_audio(self):
        from io import BytesIO
        import wave
        output=BytesIO()
        with wave.open(output,'wb') as audio:audio.setnchannels(1);audio.setsampwidth(2);audio.setframerate(22050);audio.writeframes(b'\0\0'*2205)
        code,data,_=self.request('/api/admin/audio','POST',{'data':base64.b64encode(output.getvalue()).decode()},self.admin)
        self.assertEqual(code,201);self.assertEqual(self.request(data['url'])[1][:4],b'RIFF')
        self.assertEqual(self.request('/api/admin/audio','POST',{'data':self.encoded},self.admin)[0],400)
        self.assertEqual(len(self.request('/api/admin/guides',actor=self.admin)[1]['guides']),4)
    def test_19_private_files_and_security(self):
        for path in ['/server.py','/data/heritage.db','/assets/../../server.py','/uploads/../../server.py']:
            self.assertEqual(self.request(path)[0],404)
        self.assertEqual(self.request('/api/local-shutdown','POST',{})[0],403)
        self.assertEqual(self.request('/')[2]['X-Content-Type-Options'],'nosniff')
    def test_20_malformed_requests(self):
        self.assertEqual(self.request('/api/login','POST',raw=b'{oops')[0],400)
        self.assertEqual(self.request('/api/register','POST',[])[0],400)
    def test_21_idempotent_initialize(self):
        with db.connect() as con:before=[con.execute('SELECT COUNT(*) FROM '+table).fetchone()[0] for table in ['items','questions','users','guides']]
        db.initialize()
        with db.connect() as con:after=[con.execute('SELECT COUNT(*) FROM '+table).fetchone()[0] for table in ['items','questions','users','guides']]
        self.assertEqual(before,after)
    def test_22_logout(self):
        actor=self.login('student')
        self.assertEqual(self.request('/api/logout','POST',{},actor)[0],200)
        self.assertIsNone(self.request('/api/session',actor=actor)[1]['user'])
    def test_23_png_export(self):
        output=BytesIO();Image.new('RGB',(720,720),'#efeadf').save(output,'PNG')
        code,data,_=self.request('/api/export','POST',{'data':base64.b64encode(output.getvalue()).decode()})
        self.assertEqual(code,201)
        code,binary,headers=self.request(data['url'])
        self.assertEqual(binary[:8],b'\x89PNG\r\n\x1a\n');self.assertIn('attachment',headers['Content-Disposition'])
        self.assertEqual(self.request('/api/export','POST',{'data':self.encoded})[0],400)


if __name__=='__main__':unittest.main(verbosity=2)
