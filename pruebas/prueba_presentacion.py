"""Prueba del modo presentación: diapositivas en la pantalla, pregunta automática
en los celulares al llegar a la diapositiva, resultados, revelado y nube sin solapes."""
import asyncio,sys
from playwright.async_api import async_playwright
B="http://127.0.0.1:8000/"
fallos=[];oks=[]
def check(c,m):(oks if c else fallos).append(m);print(("✔ " if c else "✘ ")+m)
SOLAPES="""()=>{var r=[...document.querySelectorAll('#nube span')].map(s=>s.getBoundingClientRect());var n=0;
for(var i=0;i<r.length;i++)for(var j=i+1;j<r.length;j++){var a=r[i],b=r[j];var ix=Math.min(a.right,b.right)-Math.max(a.left,b.left),iy=Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top);if(ix>2&&iy>2)n++}
return [r.length,n]}"""
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
    pg=await (await br.new_context(viewport={"width":1600,"height":900})).new_page()
    pg.on("pageerror",lambda e:fallos.append("JS: "+str(e)))
    await pg.goto(B+"pantalla.html?prueba");await pg.wait_for_timeout(1500)
    await pg.evaluate("localStorage.clear()");await pg.reload();await pg.wait_for_timeout(1500)
    await pg.evaluate("document.getElementById('bReset').click();document.getElementById('bReset').click()");await pg.wait_for_timeout(1000)
    src=await pg.get_attribute(".diap img","src");check(src and src.endswith("01.webp"),"Arranca en la diapositiva 1")
    tels=[]
    for i in range(4):
      t=await (await br.new_context(viewport={"width":390,"height":820})).new_page();await t.goto(B+"index.html?c=AMOR26");tels.append(t)
    await pg.wait_for_timeout(2000)
    await pg.keyboard.press("ArrowRight");await pg.wait_for_timeout(2500)
    src=await pg.get_attribute(".diap img","src");check(src.endswith("02.webp"),"Flecha → muestra la diapositiva 2")
    txt=await tels[0].text_content("main");check("enamorado" in txt,"Al llegar a la diapositiva 2 la pregunta 1 aparece sola en el celular")
    await tels[0].click("text=Sí");await tels[1].click("text=No");await pg.wait_for_timeout(2500)
    b=await pg.text_content("#envivo");check("2" in b,"La diapositiva muestra el contador en vivo: "+b.strip())
    await pg.screenshot(path="shots/pres_d2.png")
    await pg.keyboard.press("ArrowRight");await pg.wait_for_timeout(1500)
    check(await pg.locator("#zona .barras").count()==1,"Siguiente flecha → resultados en vivo de la pregunta 1")
    await pg.keyboard.press("Space");await pg.wait_for_timeout(1500)
    check("TEC" in await pg.text_content("#zona"),"Espacio revela el dato del TEC")
    await pg.screenshot(path="shots/pres_r1.png")
    await pg.keyboard.press("ArrowRight");await pg.wait_for_timeout(2500)
    src=await pg.get_attribute(".diap img","src");check(src.endswith("03.webp"),"Siguiente flecha → diapositiva 3")
    check("Estás dentro" in await tels[0].text_content("main"),"Entre preguntas el celular queda esperando")
    await pg.keyboard.press("ArrowLeft");await pg.wait_for_timeout(1200)
    check("TEC" in await pg.text_content("#zona"),"Flecha ← vuelve a los resultados (ya revelados)")
    await pg.keyboard.press("ArrowRight");await pg.keyboard.press("ArrowRight");await pg.wait_for_timeout(2500)
    check((await pg.get_attribute(".diap img","src")).endswith("04.webp"),"Diapositiva 4 (pregunta 2)")
    for t,w in zip(tels,["ok","amor","ay","okay"]):
      await t.fill("#w",w);await t.click("#ok")
    await pg.wait_for_timeout(2000)
    await pg.keyboard.press("ArrowRight");await pg.wait_for_timeout(1500)
    n,sol=await pg.evaluate(SOLAPES);check(n==4 and sol==0,f"Nube con 4 palabras parecidas: {n} palabras, {sol} solapes")
    await pg.screenshot(path="shots/pres_nube4.png")
    await pg.evaluate("document.getElementById('bSim').click()");await pg.wait_for_timeout(5000)
    n,sol=await pg.evaluate(SOLAPES);check(sol==0,f"Nube con muchas palabras: {n} palabras, {sol} solapes")
    await pg.keyboard.press("Space");await pg.wait_for_timeout(1000);await pg.keyboard.press("Space");await pg.wait_for_timeout(1500)
    n,sol=await pg.evaluate(SOLAPES);check(sol==0,f"Tras revelar/ocultar sigue sin solapes ({n} palabras)")
    await pg.screenshot(path="shots/pres_nube.png")
    # recorrer hasta el final
    for _ in range(40):await pg.keyboard.press("ArrowRight")
    await pg.wait_for_timeout(2500)
    check((await pg.get_attribute(".diap img","src")).endswith("25.webp"),"Llega a la última diapositiva (25)")
    check("Gracias" in await tels[0].text_content("main"),"En la última diapositiva el celular dice gracias")
    await pg.keyboard.press("i");await pg.wait_for_timeout(800)
    check(await pg.locator(".portada .qrg").count()==1,"Tecla I muestra la portada con el QR")
    await br.close()
  print(f"\n{len(oks)} OK, {len(fallos)} fallos");[print(" -",f) for f in fallos];sys.exit(1 if fallos else 0)
asyncio.run(main())
