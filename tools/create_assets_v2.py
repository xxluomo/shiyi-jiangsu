"""江苏非遗创意示意插画。原生SVG可编辑，不作为实物照片或精确工艺图。"""
from pathlib import Path
import ast
import re
import math

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'static'/'assets'
OUT.mkdir(parents=True, exist_ok=True)

# 只解析原有插画字符串，不导入旧脚本，避免执行其写文件副作用。
OLD = {}
for node in ast.parse((ROOT/'tools'/'create_assets.py').read_text(encoding='utf-8')).body:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        if node.targets[0].id in {'DEFS','POT','CLAY','EMBROIDERY','BAMBOO'}:
            OLD[node.targets[0].id] = ast.literal_eval(node.value)

DEFS = OLD['DEFS'] + '''<defs>
<linearGradient id="silk" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#d7c6a0"/><stop offset=".5" stop-color="#eee2bf"/><stop offset="1" stop-color="#af875a"/></linearGradient>
<linearGradient id="indigo" x1="0" x2="1" y2="1"><stop stop-color="#244d66"/><stop offset=".5" stop-color="#173e57"/><stop offset="1" stop-color="#0d2e48"/></linearGradient>
<linearGradient id="lacquer" x1="0" x2="1" y2="1"><stop stop-color="#a84235"/><stop offset=".55" stop-color="#692b29"/><stop offset="1" stop-color="#3d2628"/></linearGradient>
<linearGradient id="wood" x2="1" y2="1"><stop stop-color="#b58655"/><stop offset="1" stop-color="#704b33"/></linearGradient>
<linearGradient id="jade" x2="1" y2="1"><stop stop-color="#62938b"/><stop offset="1" stop-color="#23554e"/></linearGradient>
<pattern id="threads" width="6" height="6" patternUnits="userSpaceOnUse"><path d="M0 1H6M1 0V6" stroke="#fcf0d3" opacity=".22" stroke-width=".7"/></pattern>
<pattern id="weave" width="40" height="44" patternUnits="userSpaceOnUse"><path d="M20 1L39 22L20 43L1 22Z" fill="none" stroke="#c69d5d" stroke-width="1.5"/><path d="M20 10L30 22L20 34L10 22Z" fill="#a34e3d" opacity=".5"/></pattern>
<pattern id="blueflower" width="112" height="112" patternUnits="userSpaceOnUse"><g transform="translate(56 56)" fill="#f1e9d3"><ellipse ry="23" rx="8" cy="-15"/><ellipse ry="23" rx="8" cy="-15" transform="rotate(60)"/><ellipse ry="23" rx="8" cy="-15" transform="rotate(120)"/><ellipse ry="23" rx="8" cy="-15" transform="rotate(180)"/><ellipse ry="23" rx="8" cy="-15" transform="rotate(240)"/><ellipse ry="23" rx="8" cy="-15" transform="rotate(300)"/><circle r="8" fill="#174763"/><circle r="3"/></g><circle cx="0" cy="0" r="5" fill="#f1e9d3"/></pattern>
</defs>'''


def petals(cx,cy,r,petal,fill, count=8):
    return ''.join(f'<ellipse cx="{cx}" cy="{cy-r}" rx="{petal}" ry="{r*.62}" fill="{fill}" transform="rotate({360*i/count} {cx} {cy})"/>' for i in range(count))


def flower(cx,cy,scale=1,color='#b56456'):
    return f'<g transform="translate({cx} {cy}) scale({scale})">'+petals(0,0,24,12,color,8)+'<circle r="13" fill="#c5a463"/><circle r="5" fill="#ead5a1"/></g>'


SHADOW='<ellipse cx="360" cy="640" rx="210" ry="23" fill="#4c5c4e" opacity=".12" filter="url(#shadow)"/>'
LOOM = SHADOW + '''<path d="M162 259L505 194L563 576L210 645Z" fill="#8b6547"/>
<path d="M185 251L478 197L532 553L228 612Z" fill="#caa66d"/>
<path d="M215 287L475 239L505 459L245 516Z" fill="#e9d8ae"/>
<path d="M236 356L486 308L511 473L259 526Z" fill="url(#weave)"/>
<path d="M176 203L206 202L253 645L222 652Z M483 158L513 158L570 602L538 611Z" fill="url(#wood)"/>
<path d="M153 221L527 148L532 181L160 254Z M197 562L575 487L580 523L202 601Z" fill="#8e6241"/>
<path d="M217 584L236 695M535 521L568 640" stroke="#6c4d36" stroke-width="22"/>
<path d="M165 264L519 194" stroke="#e5c58d" stroke-width="6"/>
<path d="M245 516Q357 493 505 459L516 563Q387 642 269 612Z" fill="url(#silk)"/>
<path d="M245 516Q357 493 505 459L516 563Q387 642 269 612Z" fill="url(#weave)"/>
<path d="M257 533Q381 533 508 483M265 558Q381 558 512 511M269 585Q381 585 516 540" stroke="#c59b68" fill="none" opacity=".4"/>
<path d="M286 309Q348 279 423 285Q374 315 304 320Z" fill="#7d4731" stroke="#d7b778" stroke-width="2"/>
<ellipse cx="357" cy="301" rx="22" ry="10" fill="#d6b67d"/>
<path d="M181 256L185 276M199 253L203 272M219 249L222 268M239 245L243 264M259 241L263 260M279 237L283 256M299 233L303 252M319 229L323 248M339 225L343 244M359 221L363 240M379 217L383 236M399 213L403 232M419 209L423 228M439 205L443 224M459 201L463 220M479 197L483 216" stroke="#f3e3c4" stroke-width="2"/>
<circle cx="170" cy="235" r="5" fill="#dfbc75"/><circle cx="518" cy="168" r="5" fill="#dfbc75"/>'''

def papercut():
    p=['<circle cx="360" cy="380" r="218" fill="#a73e33"/>','<circle cx="360" cy="380" r="201" fill="#f2e8ce"/>','<circle cx="360" cy="380" r="188" fill="none" stroke="#a73e33" stroke-width="11"/>']
    for i in range(16):
        a=2*math.pi*i/16
        x,y=360+207*math.sin(a),380+207*math.cos(a)
        p.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="#f2e8ce"/>')
    for i in range(8):
        p.append(f'<g transform="rotate({i*45} 360 380)"><path d="M360 207Q301 257 338 320L360 352L382 320Q419 257 360 207Z" fill="#a73e33"/><path d="M360 231Q332 267 352 301L360 316L368 301Q388 267 360 231Z" fill="#f2e8ce"/><path d="M360 207V352" stroke="#a73e33" stroke-width="7"/></g>')
    p += ['<circle cx="360" cy="380" r="66" fill="#a73e33"/>',petals(360,380,34,12,'#f2e8ce',8),'<circle cx="360" cy="380" r="17" fill="#a73e33"/>', '<path d="M193 526Q132 603 177 650M203 536Q254 585 216 640" fill="none" stroke="#786e5f" stroke-width="8"/><circle cx="180" cy="627" r="29" fill="none" stroke="#786e5f" stroke-width="8"/><circle cx="216" cy="623" r="23" fill="none" stroke="#786e5f" stroke-width="8"/><path d="M188 593L280 499M199 601L291 507" stroke="#a5aaa1" stroke-width="7"/>']
    return SHADOW+''.join(p)

SU = '''<circle cx="360" cy="381" r="229" fill="#b18c5c"/><circle cx="360" cy="381" r="214" fill="#eee3cb"/><circle cx="360" cy="381" r="206" fill="url(#threads)"/><circle cx="360" cy="381" r="203" fill="none" stroke="#bea376" stroke-dasharray="3 5"/>
<path d="M279 540Q373 397 413 271M332 463Q431 438 478 377M363 395Q285 367 251 315" stroke="#5d7e5b" fill="none" stroke-width="6"/>
<path d="M322 476Q260 478 246 429Q302 428 322 476M351 426Q416 402 416 353Q361 364 351 426M397 440Q437 494 483 467Q447 426 397 440" fill="#7f966d" stroke="#5e7b58" stroke-width="2"/>'''+flower(408,294,1.4,'#ba756d')+flower(260,337,.9,'#d9ae81')+'''<path d="M346 137V118H376V137" fill="none" stroke="#8c7047" stroke-width="6"/><rect x="337" y="136" width="48" height="18" rx="3" fill="#a58a60"/>
<path d="M500 529L561 660" stroke="#939c95" stroke-width="3"/><path d="M543 620Q613 535 530 520" fill="none" stroke="#ba756d" stroke-width="3"/>'''

CROWN = SHADOW+'''<path d="M201 446Q188 302 258 216Q359 146 463 216Q531 300 516 446Z" fill="#ebe3cd"/>
<path d="M203 434Q360 389 516 434L498 468Q357 441 220 468Z" fill="#99443b"/>
<path d="M219 367Q357 281 499 367L486 424Q356 386 234 424Z" fill="#284f63"/>
<path d="M252 242L287 322L326 222L360 316L395 222L434 322L468 242" fill="none" stroke="#c3a45f" stroke-width="19" stroke-linejoin="round"/>
<path d="M250 242Q356 174 469 242" fill="none" stroke="#ba9d62" stroke-width="12"/>
<g fill="#b95548" stroke="#dfc68f" stroke-width="4"><circle cx="250" cy="241" r="15"/><circle cx="327" cy="217" r="16"/><circle cx="395" cy="217" r="16"/><circle cx="469" cy="241" r="15"/><circle cx="361" cy="181" r="20"/></g>
<g fill="#eee1bc"><circle cx="268" cy="277" r="6"/><circle cx="289" cy="263" r="6"/><circle cx="312" cy="251" r="6"/><circle cx="361" cy="258" r="8"/><circle cx="411" cy="251" r="6"/><circle cx="434" cy="263" r="6"/><circle cx="455" cy="277" r="6"/></g>
<path d="M221 433Q175 469 192 541 M495 433Q542 469 525 541" fill="none" stroke="#c3a45f" stroke-width="6"/>
<path d="M189 516L179 576M198 515L202 577M519 514L514 575M528 514L540 575" stroke="#b54d41" stroke-width="6"/>
<path d="M296 616L181 535Q358 401 540 535L424 616Z" fill="#efe6cd" stroke="#b49a65" stroke-width="3"/>
<path d="M360 617L217 535M360 617L264 511M360 617L310 496M360 617L360 491M360 617L410 496M360 617L457 511M360 617L506 535" stroke="#b49a65" stroke-width="2"/>
<path d="M227 555Q359 450 494 555" fill="none" stroke="#d0ba89" stroke-width="3"/>'''

PRINT = SHADOW+'''<path d="M151 337L465 266L552 503L229 581Z" fill="#5d4937"/><path d="M155 313L469 243L552 480L229 557Z" fill="url(#wood)" stroke="#60452f" stroke-width="3"/>
<path d="M177 328L456 266L527 465L241 532Z" fill="#312e28"/>
<path d="M196 338L442 283L505 450L254 509Z" fill="none" stroke="#b38a58" stroke-width="5"/>
<g stroke="#ba9566" fill="none" stroke-width="6"><path d="M240 348L291 336M258 337L286 421M241 384L306 370M254 427L309 414M338 327L388 316M354 319L380 398M332 352L400 337M354 400L413 386M441 314L477 417"/></g>
<path d="M353 497L558 449L606 582L396 635Z" fill="#f4e8cd" stroke="#d1c4a9" stroke-width="2"/>
<path d="M379 518L547 478M388 542L555 501M397 564L564 524M406 588L573 547" stroke="#656758" stroke-width="3"/>
<path d="M159 246L178 235L286 447L267 458Z" fill="#91683d"/><path d="M151 225L179 212L203 259L174 274Z" fill="#c7bb91"/><path d="M149 224L161 212L180 210L187 219L178 225L174 239L164 233L161 244Z" fill="#e7ddbd"/>
<ellipse cx="538" cy="304" rx="43" ry="25" fill="#343c35"/><ellipse cx="538" cy="298" rx="39" ry="20" fill="#1e2925"/>'''

LACQUER = SHADOW+'''<path d="M188 350Q360 279 533 350L520 552Q360 631 201 552Z" fill="url(#lacquer)" stroke="#412829" stroke-width="3"/>
<ellipse cx="360" cy="350" rx="172" ry="75" fill="#6a302e" stroke="#b58b58" stroke-width="5"/>
<ellipse cx="360" cy="336" rx="177" ry="78" fill="url(#lacquer)" stroke="#4d2c2a" stroke-width="3"/>
<ellipse cx="360" cy="329" rx="157" ry="65" fill="none" stroke="#c49c60" stroke-width="3"/>
<path d="M217 404Q359 471 504 404M215 520Q360 585 506 520" stroke="#c49c60" fill="none" stroke-width="3"/>
<path d="M297 362Q354 314 411 313" stroke="#cbb688" fill="none" stroke-width="3"/>
<path d="M316 347Q287 313 312 299Q337 308 316 347M373 326Q389 293 416 305Q401 331 373 326" fill="#c5ba8e"/>
<g transform="translate(356 329) scale(1.2 .65)">'''+petals(0,0,25,14,'#d7c897',9)+'''<circle r="15" fill="#aa744f"/></g>
<path d="M245 453Q302 472 343 483M370 483Q427 474 476 453" stroke="#d2b474" fill="none" stroke-width="2"/>
<path d="M355 414L369 414L369 445L355 445Z" fill="#b7995f"/><circle cx="362" cy="427" r="3" fill="#5f482e"/>'''

BLUE = SHADOW+'''<path d="M177 198L526 228L546 592Q369 660 187 605Z" fill="url(#indigo)" stroke="#1e3a4a" stroke-width="3"/>
<path d="M177 198L526 228L546 592Q369 660 187 605Z" fill="url(#blueflower)"/>
<path d="M177 198L231 221L237 606L187 605Z" fill="#e6dcc5" opacity=".17"/>
<path d="M448 221L481 223L503 604L467 616Z" fill="#071d2b" opacity=".2"/>
<path d="M197 214L511 244M199 227L513 257M207 578Q360 632 528 578M208 588Q360 642 529 588" stroke="#dfd8bf" fill="none" stroke-width="3"/>
<path d="M225 233L270 229L287 597L236 606Z" fill="#a1b2b0" opacity=".13"/>
<path d="M148 632Q192 585 276 640L307 694Q209 657 148 678Z" fill="#d0c2a1" stroke="#b7a47b" stroke-width="2"/>
<path d="M179 638L192 657M198 635L211 654M218 640L231 660M238 648L251 669M258 657L270 678" stroke="#8f805f" stroke-width="2"/>'''

SACHET = SHADOW+'''<path d="M316 257Q279 203 294 165Q317 131 343 181L360 227Q379 130 412 159Q439 190 400 250" fill="none" stroke="#b29458" stroke-width="8"/>
<path d="M291 279Q360 264 430 279L460 474Q449 556 360 578Q271 556 260 474Z" fill="url(#jade)" stroke="#28594e" stroke-width="3"/>
<path d="M291 279Q360 247 430 279L422 316Q360 297 299 316Z" fill="#c6aa69"/>
<path d="M304 323Q361 307 416 323L438 473Q428 534 360 554Q290 533 281 473Z" fill="none" stroke="#c6aa69" stroke-width="4"/>
<path d="M356 547L356 624M367 547L367 624" stroke="#c7a764" stroke-width="5"/>
<path d="M344 619L338 685M353 619L351 691M362 619L364 693M371 619L377 687M380 619L390 678" stroke="#b75443" stroke-width="7"/>
<ellipse cx="362" cy="620" rx="20" ry="12" fill="#c7a764"/>
<path d="M334 493Q364 429 392 379" stroke="#c2be85" fill="none" stroke-width="4"/>
<path d="M354 450Q309 441 316 407Q352 411 354 450M374 418Q422 412 420 384Q384 385 374 418" fill="#b4bf91"/>'''+flower(390,374,.9,'#d0a87d')+flower(333,465,.65,'#dfc68e')

def strip_text(body):
    return re.sub(r'<text\b.*?</text>', '', body, flags=re.S)


ITEMS = {
    'yunjin': ('南京云锦意象', LOOM, '#e9e0cd'),
    'papercut': ('南京剪纸意象', papercut(), '#f0e5cf'),
    'suxiu': ('苏绣意象', SU, '#e4e7db'),
    'kunqu': ('昆曲戏冠与折扇意象', CROWN, '#e7ddd3'),
    'clay': ('惠山泥人意象', strip_text(OLD['CLAY']), '#e9dfcb'),
    'teapot': ('宜兴紫砂壶意象', strip_text(OLD['POT']), '#e3e6d8'),
    'embroidery': ('无锡精微绣意象', strip_text(OLD['EMBROIDERY']), '#e4e9df'),
    'bamboo': ('留青竹刻意象', strip_text(OLD['BAMBOO']), '#dedfcf'),
    'printing': ('雕版印刷意象', PRINT, '#e9e1d1'),
    'lacquer': ('扬州漆器意象', LACQUER, '#e1dfd2'),
    'bluecloth': ('蓝印花布意象', BLUE, '#e1e4db'),
    'sachet': ('徐州香包意象', SACHET, '#e9e0ce'),
}

def frame(body, title, bg, detail=False):
    width,height=(1000,720) if detail else (720,800)
    art=f'<g transform="translate(-75 -165) scale(1.65)">{body}</g>' if detail else body
    # 细节图是同一示意插画的放大构图，强调不是实物微距照片。
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img"><title>{title} · {'局部' if detail else '主题'}示意插画</title>{DEFS}<rect width="{width}" height="{height}" fill="{bg}"/><circle cx="{width*.5}" cy="{height*.43}" r="{height*.34}" fill="#f6eedc" opacity=".5"/>{art}<rect width="{width}" height="{height}" fill="url(#grain)"/><path d="M30 63V30H63M{width-63} 30H{width-30}V63M30 {height-63}V{height-30}H63M{width-63} {height-30}H{width-30}V{height-63}" stroke="#9f977f" stroke-width="1" opacity=".35" fill="none"/></svg>'''


if __name__ == '__main__':
    files=[]
    for slug,(title,body,bg) in ITEMS.items():
        cover=f'{slug}-v2.svg' if slug in {'clay','teapot','embroidery','bamboo'} else f'{slug}.svg'
        for name,detail in [(cover,False),(slug+'-detail.svg',True)]:
            (OUT/name).write_text(frame(body,title,bg,detail),encoding='utf-8')
            files.append(name)
    print('Created',len(files),'SVG assets:\n'+'\n'.join(files))
