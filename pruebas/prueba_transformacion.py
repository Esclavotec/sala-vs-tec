"""Prueba de la Transformación (Morph): los elementos viajan entre diapositivas,
terminan en la diapositiva correcta y después corren las animaciones."""
import asyncio,sys
from playwright.async_api import async_playwright
B="http://127.0.0.1:8000/";fallos=[];oks=[]
def check(c,m):(oks if c else fallos).append(m);print(("✔ " if c else "✘ ")+m)
async def ir_a(pg,n):
    for _ in range(90):
        if (await pg.text_content(".dnum")).startswith(f"Diapositiva {n} /"):return
        await pg.keyboard.press("ArrowRight");await pg.wait_for_timeout(90)
async def estado(pg):return await pg.evaluate("""(()=>{var l=document.querySelector('.diap:last-child .lienzo');
  return {mf:l.querySelectorAll('.mf').length, imgs:[...l.querySelectorAll(':scope > img')].map(i=>i.getAttribute('src').split('/').pop()),
  r:[...l.querySelectorAll('.mf')].map(e=>{var a=e.getBoundingClientRect(),b=l.getBoundingClientRect();return [(a.left-b.left)/b.width*100,(a.top-b.top)/b.height*100]})}})()""")
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
    pg=await (await br.new_context(viewport={"width":1920,"height":1080})).new_page()
    pg.on("pageerror",lambda e:fallos.append("JS: "+str(e)))
    await pg.goto(B+"pantalla.html");await pg.wait_for_timeout(600)
    await pg.evaluate("localStorage.clear()");await pg.reload();await pg.wait_for_timeout(1500)
    await ir_a(pg,3);await pg.wait_for_timeout(1600)
    await pg.keyboard.press("ArrowRight");await pg.wait_for_timeout(150);e0=await estado(pg)
    await pg.wait_for_timeout(450);e1=await estado(pg);await pg.screenshot(path="shots/morf_3a4_mitad.png")
    await pg.wait_for_timeout(1000);e2=await estado(pg)
    check(e0["mf"]==4,f"3→4: se transforman 4 elementos (imagen, número, título, subtítulo): {e0['mf']}")
    mov=e0["r"] and e1["r"] and abs(e0["r"][0][0]-e1["r"][0][0])>3
    check(bool(mov),f"3→4: los elementos se mueven (x {e0['r'][0][0]:.0f}% → {e1['r'][0][0]:.0f}%)")
    check(e2["mf"]==0 and e2["imgs"]==["04.webp"],f"3→4: termina en la diapositiva 4 completa: {e2['imgs']}")
    await ir_a(pg,9);await pg.wait_for_timeout(1300);await pg.keyboard.press("ArrowRight");await pg.wait_for_timeout(500)
    e=await estado(pg);await pg.screenshot(path="shots/morf_9a10_mitad.png")
    check(e["mf"]==1,"9→10: la etiqueta 'Cap.' se transforma hacia la diapositiva de votación")
    await pg.wait_for_timeout(1200)
    await ir_a(pg,19);await pg.wait_for_timeout(3200);await pg.keyboard.press("ArrowRight");await pg.wait_for_timeout(500)
    e=await estado(pg);check(e["mf"]==1,"19→20: la etiqueta 'Cap. IV' se transforma")
    await pg.wait_for_timeout(1000);await pg.wait_for_timeout(2200)
    n=await pg.locator(".diap:last-child .lienzo img").count()
    check(n==5,f"19→20: al terminar la Transformación corren las 4 animaciones automáticas ({n} capas)")
    await pg.keyboard.press("ArrowLeft");await pg.wait_for_timeout(400);e=await estado(pg)
    check(e["mf"]==0,"Al volver atrás no se transforma (igual que PowerPoint)")
    await ir_a(pg,24);await pg.wait_for_timeout(1300);await pg.keyboard.press("ArrowRight");await pg.wait_for_timeout(500)
    e=await estado(pg);await pg.screenshot(path="shots/morf_24a25_mitad.png")
    check(e["mf"]==1,"24→25: la pareja se transforma hacia 'Muchas gracias'")
    await pg.keyboard.press("ArrowRight");await pg.wait_for_timeout(200);e=await estado(pg)
    check(e["mf"]==0,"Presionar → durante la Transformación la termina al instante")
    await br.close()
  print(f"\n{len(oks)} OK, {len(fallos)} fallos");[print(" -",f) for f in fallos];sys.exit(1 if fallos else 0)
asyncio.run(main())
