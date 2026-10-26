"""拾遗江苏：SQLite表结构、兼容迁移和内容初始化。"""
from pathlib import Path
import hashlib
import json
import secrets
import sqlite3

ROOT = Path(__file__).resolve().parent
DATA = ROOT/'data'
DB = DATA/'heritage.db'
UPLOADS = DATA/'uploads'
CATEGORIES = ['传统美术', '传统技艺', '传统戏剧']
THEMES = ['丝线经纬', '纸墨纹样', '泥竹器物', '戏韵民俗']
CITIES = ['南京', '苏州', '无锡', '扬州', '南通', '徐州']


class Database(sqlite3.Connection):
    def __exit__(self, *args):
        try:
            return super().__exit__(*args)
        finally:
            self.close()


def connect():
    con = sqlite3.connect(DB, timeout=20, factory=Database)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys=ON')
    return con


def hashed(password, salt):
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 260000).hex()


def add_columns(con, table, columns):
    current = {row[1] for row in con.execute('PRAGMA table_info('+table+')')}
    for name, definition in columns.items():
        if name not in current:
            con.execute('ALTER TABLE '+table+' ADD COLUMN '+name+' '+definition)


def unpack_item(row):
    obj = dict(row)
    for key in ['steps', 'gallery', 'tags']:
        obj[key] = json.loads(obj.get(key) or '[]')
    # Upgrade graphics without replacing existing editable source assets.
    candidate = ROOT/'static/assets'/((obj.get('slug') or '')+'-v2.svg')
    if candidate.is_file() and obj['image'].endswith('/'+obj['slug']+'.svg'):
        obj['image'] = '/assets/'+candidate.name
    if not obj['gallery']:
        obj['gallery'] = [obj['image']]
    else:
        obj['gallery'][0] = obj['image']
    return obj


def initialize():
    UPLOADS.mkdir(parents=True, exist_ok=True)
    with connect() as con:
        con.executescript('''
        CREATE TABLE IF NOT EXISTS items(id INTEGER PRIMARY KEY AUTOINCREMENT,
          title TEXT NOT NULL,category TEXT NOT NULL,region TEXT NOT NULL,summary TEXT NOT NULL,
          content TEXT NOT NULL,steps TEXT NOT NULL,image TEXT NOT NULL,source_url TEXT NOT NULL,
          source_name TEXT NOT NULL,updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS questions(id INTEGER PRIMARY KEY AUTOINCREMENT,
          prompt TEXT NOT NULL,options TEXT NOT NULL,answer INTEGER NOT NULL,explanation TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS attempts(id INTEGER PRIMARY KEY AUTOINCREMENT,score INTEGER NOT NULL,
          total INTEGER NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS quiz_tickets(token TEXT PRIMARY KEY,question_ids TEXT NOT NULL,expires REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,username TEXT UNIQUE NOT NULL,
          nickname TEXT NOT NULL,salt TEXT NOT NULL,password_hash TEXT NOT NULL,
          role TEXT NOT NULL DEFAULT 'member',created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS auth_sessions(token_hash TEXT PRIMARY KEY,user_id INTEGER NOT NULL
          REFERENCES users(id) ON DELETE CASCADE,csrf TEXT NOT NULL,expires REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS favorites(user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
          item_id INTEGER REFERENCES items(id) ON DELETE CASCADE,created_at TEXT DEFAULT CURRENT_TIMESTAMP,
          PRIMARY KEY(user_id,item_id));
        CREATE TABLE IF NOT EXISTS progress(user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
          item_id INTEGER REFERENCES items(id) ON DELETE CASCADE,step INTEGER NOT NULL DEFAULT 0,
          completed INTEGER NOT NULL DEFAULT 0,updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
          PRIMARY KEY(user_id,item_id));
        CREATE TABLE IF NOT EXISTS works(id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,title TEXT NOT NULL,
          kind TEXT NOT NULL,params TEXT NOT NULL,image TEXT NOT NULL,thumb TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS guides(id INTEGER PRIMARY KEY AUTOINCREMENT,slug TEXT UNIQUE NOT NULL,
          title TEXT NOT NULL,item_slug TEXT NOT NULL,text TEXT NOT NULL,src TEXT NOT NULL,
          voice TEXT NOT NULL,kind TEXT NOT NULL DEFAULT 'synthetic');
        CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        ''')
        add_columns(con, 'items', {'slug':"TEXT NOT NULL DEFAULT ''", 'city':"TEXT NOT NULL DEFAULT '无锡'",
          'theme':"TEXT NOT NULL DEFAULT '泥竹器物'", 'material':"TEXT NOT NULL DEFAULT ''",
          'tags':"TEXT NOT NULL DEFAULT '[]'", 'gallery':"TEXT NOT NULL DEFAULT '[]'",'published':'INTEGER NOT NULL DEFAULT 1'})
        add_columns(con, 'questions', {'topic':"TEXT NOT NULL DEFAULT '综合知识'"})
        add_columns(con, 'attempts', {'user_id':'INTEGER REFERENCES users(id) ON DELETE SET NULL',
          'details':"TEXT NOT NULL DEFAULT '[]'"})
        add_columns(con, 'quiz_tickets', {'user_id':'INTEGER REFERENCES users(id) ON DELETE CASCADE',
          'snapshot':"TEXT NOT NULL DEFAULT '[]'"})
        if not con.execute("SELECT 1 FROM meta WHERE key='jiangsu_v2'").fetchone():
            content_path = ROOT/'content_v2.json'
            if not content_path.exists():
                raise RuntimeError('content_v2.json尚未准备好')
            data = json.loads(content_path.read_text(encoding='utf-8'))
            aliases = {'teapot':'宜兴紫砂陶制作技艺','clay':'惠山泥人','embroidery':'无锡精微绣','bamboo':'无锡留青竹刻'}
            fields = ['title','category','region','summary','content','steps','image','source_url','source_name',
                      'slug','city','theme','material','tags','gallery']
            for item in data['items']:
                values = {k:item.get(k, '') for k in fields}
                for key in ['steps','tags','gallery']:
                    values[key] = json.dumps(item.get(key,[]),ensure_ascii=False)
                old = con.execute('SELECT id FROM items WHERE slug=? OR title=?',
                    (item['slug'],aliases.get(item['slug'],item['title']))).fetchone()
                if old:
                    con.execute('UPDATE items SET '+','.join(f'{k}=:{k}' for k in fields)+' WHERE id=:id',
                                {**values,'id':old['id']})
                else:
                    con.execute('INSERT INTO items('+','.join(fields)+') VALUES('+','.join(':'+k for k in fields)+')',values)
            # Replace only the original bundled questions, keeping any custom questions.
            old_seed = json.loads((ROOT/'seed.json').read_text(encoding='utf-8')) if (ROOT/'seed.json').exists() else {}
            for q in old_seed.get('questions',[]):
                con.execute('DELETE FROM questions WHERE prompt=?',(q['prompt'],))
            for q in data['questions']:
                con.execute('INSERT INTO questions(prompt,options,answer,explanation,topic) VALUES(?,?,?,?,?)',
                  (q['prompt'],json.dumps(q['options'],ensure_ascii=False),q['answer'],q['explanation'],q.get('topic','综合知识')))
            for username,nickname,role in [('admin','策展管理员','admin'),('student','非遗探索者','member')]:
                salt = secrets.token_hex(16)
                con.execute('INSERT INTO users(username,nickname,salt,password_hash,role) VALUES(?,?,?,?,?) '
                  'ON CONFLICT(username) DO UPDATE SET salt=excluded.salt,password_hash=excluded.password_hash',
                  (username,nickname,salt,hashed('123456',salt),role))
            # Explicitly requested local demo password migration, including legacy account data.
            if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='admins'").fetchone():
                for admin in con.execute('SELECT id,salt FROM admins').fetchall():
                    con.execute('UPDATE admins SET password_hash=? WHERE id=?',(hashed('123456',admin['salt']),admin['id']))
            con.execute("INSERT INTO meta VALUES('jiangsu_v2','1')")
        if not con.execute("SELECT 1 FROM meta WHERE key='v2_publish'").fetchone():
            con.execute("UPDATE items SET published=0 WHERE slug='' ")
            con.execute("INSERT INTO meta VALUES('v2_publish','1')")
        if (ROOT/'audio_guides.json').exists():
            audio = json.loads((ROOT/'audio_guides.json').read_text(encoding='utf-8'))
            for g in audio['guides']:
                con.execute('INSERT OR IGNORE INTO guides(slug,title,item_slug,text,src,voice,kind) VALUES(?,?,?,?,?,?,?)',
                  (g['slug'],g['title'],g['item_slug'],g['text'],g['src'],g['voice'],g.get('kind','synthetic')))
