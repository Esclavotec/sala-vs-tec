"""Prueba de la franja superior y de las animaciones recreadas del PowerPoint."""
import asyncio,sys
from playwright.async_api import async_playwright
B="http://127.0.0.1:8000/";fallos=[];oks=[]
def check(c,m):(oks if c else fallos).append(m);print(("✔ " if c else "✘ ")+m)
async def ir_a(pg,n):
    # avanza desde el inicio hasta la diapositiva n (salta resultados y animaciones por clic)
    for _ in range(80):
        t=await pg.text_content(".dnum")
        if t.startswith(f"Diapositiva {n} /"):return
        await pg.keyboard.press("ArrowRight");await pg.wait_for_timeout(120)
async def capas(pg):return await pg.locator(".diap:last-child .lienzo img").count()
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
    pg=await (await br.new_context(viewport={"width":1920,"height":1080})).new_page()
    pg.on("pageerror",lambda e:fallos.append("JS: "+str(e)))
    await pg.goto(B+"pantalla.html");await pg.wait_for_timeout(800)
    await pg.evaluate("localStorage.clear()");await pg.reload();await pg.wait_for_timeout(1500)
    # franja: la diapositiva empieza debajo de la barra y nada la tapa
    bar=await pg.evaluate("document.querySelector('footer').getBoundingClientRect().bottom")
    lz=await pg.evaluate("(()=>{var r=document.querySelector('.diap:last-child .lienzo').getBoundingClientRect();return [r.top,r.bottom,r.left,r.right]})()")
    check(lz[0]>=bar-1 and lz[1]<=1080.5,f"La diapositiva queda debajo de la franja negra (barra hasta {bar:.0f}px, diapositiva {lz[0]:.0f}–{lz[1]:.0f}px)")
    await ir_a(pg,2);await pg.wait_for_timeout(1200)
    tapa=await pg.evaluate("(()=>{var e=document.getElementById('envivoTop').getBoundingClientRect(),l=document.querySelector('.diap:last-child .lienzo').getBoundingClientRect();return [getComputedStyle(document.getElementById('envivoTop')).display, e.bottom<=l.top+1]})()")
    check(tapa[0]!="none" and tapa[1],"El contador EN VIVO está en la franja y no tapa la diapositiva")
    await pg.screenshot(path="shots/anim_d2.png")
    await ir_a(pg,4);await pg.keyboard.press("ArrowRight");await pg.wait_for_timeout(150);await pg.keyboard.press("ArrowRight");await pg.wait_for_timeout(100);n0=await capas(pg)
    await pg.wait_for_timeout(2200);n1=await capas(pg)
    check(n0==1 and n1==4,f"Diap 5: animaciones automáticas (capas {n0} → {n1})")
    await ir_a(pg,13);await pg.wait_for_timeout(1600);a=await capas(pg)
    await pg.keyboard.press("ArrowRight");await pg.wait_for_timeout(800);b=await capas(pg);t=await pg.text_content(".dnum")
    check(a==1 and b==2 and t.startswith("Diapositiva 13"),f"Diap 13: el elemento aparece con clic sin cambiar de diapositiva ({a} → {b}, {t})")
    await pg.screenshot(path="shots/anim_d13.png")
    await pg.keyboard.press("ArrowRight");await pg.wait_for_timeout(600);t=await pg.text_content(".dnum")
    check(t.startswith("Resultados · pregunta 4"),"El siguiente clic ya pasa a los resultados de la pregunta 4: "+t)
    await ir_a(pg,19);await pg.wait_for_timeout(500);await pg.screenshot(path="shots/anim_d19_mitad.png")
    await pg.wait_for_timeout(2500);n=await capas(pg);await pg.screenshot(path="shots/anim_d19.png")
    check(n==7,f"Diap 19: 6 animaciones (barrido de barras + valores) → {n} capas")
    await pg.keyboard.press("ArrowRight");await pg.wait_for_timeout(300);await pg.keyboard.press("ArrowLeft");await pg.wait_for_timeout(700)
    n=await capas(pg);t=await pg.text_content(".dnum")
    check(t.startswith("Diapositiva 19") and n==1,"Al volver atrás la diapositiva se muestra completa, sin repetir animaciones")
    await br.close()
  print(f"\n{len(oks)} OK, {len(fallos)} fallos");[print(" -",f) for f in fallos];sys.exit(1 if fallos else 0)
asyncio.run(main())
