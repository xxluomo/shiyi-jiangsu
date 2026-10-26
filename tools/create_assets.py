"""生成项目原创 SVG 示意插画。图片不是非遗实物照片。"""
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / 'static' / 'assets'
OUT.mkdir(parents=True, exist_ok=True)
DEFS = '''<defs>
<linearGradient id="bg" x2="1" y2="1"><stop stop-color="#ebe8d8"/><stop offset="1" stop-color="#d5ddce"/></linearGradient>
<linearGradient id="pot" x2="0.8" y2="1"><stop stop-color="#bd7c52"/><stop offset=".5" stop-color="#9c583a"/><stop offset="1" stop-color="#693d2c"/></linearGradient>
<linearGradient id="red" x2="1" y2="1"><stop stop-color="#b95843"/><stop offset="1" stop-color="#8e302c"/></linearGradient>
<radialGradient id="face"><stop stop-color="#fff2cb"/><stop offset="1" stop-color="#e5c794"/></radialGradient>
<pattern id="grain" width="7" height="7" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r=".6" fill="#677456" opacity=".1"/></pattern>
<filter id="shadow"><feGaussianBlur stdDeviation="7"/></filter>
</defs>'''

def wrap(body, title, bg='#e8e7d8'):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="720" height="800" viewBox="0 0 720 800" role="img"><title>{title}·原创示意插画</title>{DEFS}<rect width="720" height="800" fill="{bg}"/><rect width="720" height="800" fill="url(#grain)"/>{body}</svg>'

POT = '''<ellipse cx="357" cy="566" rx="201" ry="20" fill="#53634d" opacity=".16" filter="url(#shadow)"/>
<path d="M475 367 C614 302 615 483 482 490" fill="none" stroke="#6d412f" stroke-width="28"/>
<path d="M480 369 C593 323 592 469 489 479" fill="none" stroke="#a36645" stroke-width="12"/>
<path d="M226 401 C177 411 183 351 128 336 C148 392 162 457 228 479" fill="url(#pot)" stroke="#75472e" stroke-width="2"/>
<path d="M227 373 Q355 322 485 373 L501 455 Q495 549 361 554 Q225 549 211 468 Z" fill="url(#pot)" stroke="#75472e" stroke-width="2"/>
<ellipse cx="356" cy="375" rx="130" ry="27" fill="#704730"/><ellipse cx="356" cy="366" rx="116" ry="22" fill="#ad714b"/>
<path d="M251 359 Q354 318 461 359" fill="#ad714b" stroke="#73472d" stroke-width="2"/>
<ellipse cx="356" cy="339" rx="22" ry="11" fill="#7f4c30"/><path d="M339 338 Q339 313 356 313 Q375 315 373 338" fill="url(#pot)"/>
<path d="M239 404 Q221 477 281 513" fill="none" stroke="#d49a67" stroke-width="5" opacity=".45"/>
<path d="M282 528 Q359 548 436 525" fill="none" stroke="#573c2b" opacity=".35"/>
<path d="M325 253 Q294 220 326 192 M362 249 Q389 220 366 186" stroke="#708473" stroke-width="3" fill="none" opacity=".5"/>
<path d="M277 579 Q351 597 434 579" stroke="#9aab93" fill="none"/>
<text x="359" y="651" text-anchor="middle" font-family="serif" font-size="17" fill="#5c6755" letter-spacing="9">泥 火 成 器</text>'''
CLAY = '''<circle cx="361" cy="350" r="222" fill="#edcfaa" opacity=".35"/>
<ellipse cx="360" cy="650" rx="164" ry="18" fill="#53634d" opacity=".15" filter="url(#shadow)"/>
<path d="M239 431 Q183 451 204 540 Q218 574 251 552 M482 431 Q540 451 518 540 Q502 574 468 552" fill="url(#red)" stroke="#7e372e" stroke-width="2"/>
<path d="M251 417 Q359 390 468 417 L493 600 Q482 657 360 655 Q238 655 227 600 Z" fill="url(#red)"/>
<path d="M302 426 L360 489 L419 426 L416 611 Q359 633 305 611 Z" fill="#2e655e"/>
<path d="M305 455 L360 500 L415 455" fill="none" stroke="#dfbf6c" stroke-width="5"/>
<ellipse cx="360" cy="327" rx="132" ry="124" fill="#253d36"/>
<ellipse cx="360" cy="348" rx="119" ry="110" fill="url(#face)"/>
<path d="M248 301 Q242 211 322 215 Q339 267 360 267 Q386 268 400 215 Q477 215 475 302 Q458 283 425 277 Q365 321 295 276 Q262 281 248 301" fill="#2c3e36"/>
<ellipse cx="280" cy="375" rx="24" ry="14" fill="#d57762" opacity=".45"/><ellipse cx="440" cy="375" rx="24" ry="14" fill="#d57762" opacity=".45"/>
<path d="M290 339 Q308 324 326 339 M394 339 Q412 324 430 339" fill="none" stroke="#3e3f30" stroke-width="6" stroke-linecap="round"/>
<path d="M332 381 Q360 406 390 381" fill="none" stroke="#a34438" stroke-width="6" stroke-linecap="round"/>
<path d="M359 350 L354 367 L364 367" fill="none" stroke="#b58a5a" stroke-width="3"/>
<ellipse cx="270" cy="493" rx="30" ry="23" fill="url(#face)"/><ellipse cx="451" cy="493" rx="30" ry="23" fill="url(#face)"/>
<path d="M278 493 Q360 449 444 493 L421 551 Q360 577 301 551 Z" fill="#d2a359" stroke="#b5843b" stroke-width="2"/>
<path d="M304 503 Q361 480 420 503" fill="none" stroke="#f6d78d" stroke-width="5"/>
<text x="360" y="703" text-anchor="middle" font-family="serif" font-size="17" fill="#6b6754" letter-spacing="9">泥 塑 有 情</text>'''
EMBROIDERY = '''<circle cx="360" cy="377" r="231" fill="#b18d5d"/><circle cx="360" cy="377" r="217" fill="#f4e9ce"/><circle cx="360" cy="377" r="209" fill="none" stroke="#cbb384" stroke-dasharray="3 5"/>
<path d="M269 537 Q350 408 393 269 M314 472 Q410 444 473 375 M337 409 Q275 380 246 321" fill="none" stroke="#6e875e" stroke-width="7"/>
<path d="M310 472 Q241 482 233 427 Q291 421 310 472 M345 405 Q410 379 418 328 Q355 338 345 405 M372 336 Q309 331 316 285 Q363 291 372 336 M394 436 Q436 492 481 470 Q454 422 394 436" fill="#849872" stroke="#627e58" stroke-width="2"/>
<g fill="#be6f60" stroke="#985a4c" stroke-width="2"><ellipse cx="395" cy="267" rx="24" ry="43" transform="rotate(-30 395 267)"/><ellipse cx="431" cy="274" rx="24" ry="43" transform="rotate(35 431 274)"/><ellipse cx="438" cy="313" rx="24" ry="43" transform="rotate(85 438 313)"/><ellipse cx="394" cy="325" rx="24" ry="43" transform="rotate(145 394 325)"/><ellipse cx="371" cy="296" rx="24" ry="43" transform="rotate(-65 371 296)"/></g>
<circle cx="405" cy="298" r="19" fill="#c6a155"/><g fill="#f2d999"><circle cx="399" cy="293" r="3"/><circle cx="411" cy="291" r="3"/><circle cx="409" cy="304" r="3"/><circle cx="398" cy="306" r="3"/></g>
<g fill="#e3b98b" stroke="#b79468" stroke-width="2"><ellipse cx="255" cy="326" rx="18" ry="32"/><ellipse cx="279" cy="343" rx="18" ry="32" transform="rotate(70 279 343)"/><ellipse cx="263" cy="366" rx="18" ry="32" transform="rotate(140 263 366)"/><ellipse cx="234" cy="353" rx="18" ry="32" transform="rotate(-55 234 353)"/></g><circle cx="255" cy="347" r="12" fill="#aa7952"/>
<path d="M491 528 L531 610 L548 652" stroke="#a1a6a0" stroke-width="3"/><path d="M542 639 Q593 559 523 541" stroke="#a95f50" fill="none" stroke-width="2"/>
<path d="M302 467 L278 441 M341 400 L383 365 M379 428 L448 459" stroke="#d8dfb7" stroke-width="2" stroke-dasharray="3 3"/>
<rect x="344" y="129" width="32" height="21" rx="3" fill="#967947"/><path d="M350 126 L350 111 L369 111 L369 126" stroke="#7c6950" fill="none" stroke-width="4"/>
<text x="360" y="705" text-anchor="middle" font-family="serif" font-size="17" fill="#6b6754" letter-spacing="9">丝 线 生 花</text>'''
BAMBOO = '''<ellipse cx="360" cy="644" rx="166" ry="17" fill="#53634d" opacity=".14" filter="url(#shadow)"/>
<path d="M231 198 Q357 161 487 198 L485 621 Q359 663 231 621 Z" fill="#a5814e" stroke="#7b643f" stroke-width="3"/>
<ellipse cx="359" cy="198" rx="129" ry="28" fill="#d0b780"/><ellipse cx="359" cy="198" rx="113" ry="19" fill="#7c683e"/><ellipse cx="359" cy="203" rx="107" ry="12" fill="#958151"/>
<path d="M257 224 L257 613 M275 225 L275 621 M444 226 L444 622 M466 225 L466 615" stroke="#d6ba7f" opacity=".35" fill="none"/>
<path d="M296 598 Q357 448 416 278 M333 506 L292 401 M367 418 L443 371" stroke="#e2cda0" stroke-width="6" fill="none"/>
<path d="M334 506 Q285 488 287 451 Q326 460 334 506 M353 461 Q414 449 419 413 Q372 412 353 461 M382 375 Q337 356 340 318 Q380 335 382 375 M410 294 Q456 306 461 273 Q432 266 410 294" fill="#d8c18b" stroke="#efdcb0" stroke-width="1"/>
<path d="M315 399 Q310 355 281 338 Q270 376 315 399 M406 399 Q441 414 462 390 Q446 365 406 399" fill="#d8c18b"/>
<path d="M319 348 Q367 310 405 337 Q384 366 358 361 L336 389 Z" fill="#e4d0a4"/><path d="M405 337 L424 336 L406 346" fill="#e4d0a4"/><circle cx="396" cy="335" r="3" fill="#8b7147"/>
<path d="M347 346 L327 326 L316 361" fill="none" stroke="#927646" stroke-width="2"/>
<text x="360" y="710" text-anchor="middle" font-family="serif" font-size="17" fill="#6b6754" letter-spacing="9">竹 上 留 韵</text>'''
for name, body, title, bg in [('teapot', POT, '紫砂壶', '#e4e6d8'), ('clay', CLAY, '惠山泥人意象', '#e9dfcb'), ('embroidery', EMBROIDERY, '刺绣意象', '#e4e9df'), ('bamboo', BAMBOO, '竹刻意象', '#dedfcf')]:
    (OUT / (name+'.svg')).write_text(wrap(body,title,bg),encoding='utf-8')

hero = f'''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="800" viewBox="0 0 800 800"><title>江南手艺印象 · 原创示意插画</title>{DEFS}
<rect width="800" height="800" fill="url(#bg)"/><circle cx="392" cy="319" r="216" fill="#eee9d4"/>
<path d="M0 486 Q161 378 310 471 T800 460 L800 800 L0 800" fill="#9eae97" opacity=".35"/>
<path d="M0 537 Q169 460 401 531 T800 500 L800 800 L0 800" fill="#7f967e" opacity=".3"/>
<path d="M-20 674 L800 545 L800 800 L0 800" fill="#d4ccb3"/>
<path d="M49 160 Q107 268 93 420 M76 245 Q18 230 25 192 Q72 202 76 245 M92 288 Q152 269 168 228 Q111 228 92 288 M96 346 Q49 331 46 297 Q90 310 96 346" stroke="#60795b" stroke-width="4" fill="#6e875f"/>
<g transform="translate(135 185) scale(.87)">{POT.split('<text')[0]}</g>
<g transform="translate(-19 282) scale(.48)">{CLAY.split('<text')[0]}</g>
<path d="M621 604 Q665 561 704 561" stroke="#6b805e" fill="none" stroke-width="3"/>
<path d="M657 578 Q625 564 624 540 Q653 548 657 578 M672 568 Q695 534 720 539 Q712 565 672 568" fill="#6b805e"/>
<rect width="800" height="800" fill="url(#grain)"/>
</svg>'''
(OUT/'hero.svg').write_text(hero,encoding='utf-8')
(OUT/'seal.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="6" fill="#a83e32"/><text x="32" y="47" text-anchor="middle" font-family="serif" font-size="43" fill="#fff4dc">拾</text></svg>',encoding='utf-8')
print('Created 6 original SVG assets.')
