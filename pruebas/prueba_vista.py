"""Prueba del botón 'Vista del público': se abre el celular dentro de la pantalla,
sigue las preguntas y su voto NO cuenta en los resultados (modo demo y Firebase)."""
import asyncio,sys
from playwright.async_api import async_playwright
async def caso(br,url,nombre,fallos):
    pg=await br.new_page(viewport={"width":1600,"height":900})
    pg.on("pageerror",lambda e:fallos.append(nombre+": "+str(e)))
    await pg.goto(url);await pg.wait_for_timeout(1500)
    await pg.click("#bReset");await pg.click("#bReset");await pg.wait_for_timeout(800)
    await pg.keyboard.press("ArrowRight");await pg.wait_for_timeout(800)
    await pg.keyboard.press("v");await pg.wait_for_timeout(3500)
    fr=pg.frame_locator("#vFrame")
    t=await fr.locator("main").text_content()
    ok1="enamorado" in t;print(nombre,"vista muestra la pregunta:",ok1)
    await pg.screenshot(path=f"shots/vista_{nombre}.png")
    await fr.locator(".op >> nth=0").click();await pg.wait_for_timeout(2500)
    await pg.keyboard.press("Escape");await pg.wait_for_timeout(500)
    n=await pg.text_content("#resp b");g=await pg.text_content("#nGente")
    ok2=(n=="0" and g=="0");print(nombre,"voto de la vista no cuenta (votos,gente):",n,g)
    if not(ok1 and ok2):fallos.append(nombre+" falló")
    await pg.close()
async def main():
  fallos=[]
  async with async_playwright() as p:
    br=await p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
    await caso(br,"http://127.0.0.1:8002/pantalla.html?demo&sinpresentacion","demo",fallos)
    await caso(br,"http://127.0.0.1:8000/pantalla.html?sinpresentacion","firebase",fallos)
    await br.close()
  print("fallos:",fallos);sys.exit(1 if fallos else 0)
asyncio.run(main())
