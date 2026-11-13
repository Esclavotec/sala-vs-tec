"""Prueba del modo demo (sin Firebase, sin internet): demo.html con 3 marcos."""
import asyncio,sys
from playwright.async_api import async_playwright
async def main():
  fallos=[]
  async with async_playwright() as p:
    br=await p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
    pg=await br.new_page(viewport={"width":1500,"height":800})
    pg.on("pageerror",lambda e:fallos.append(str(e)))
    await pg.goto("http://127.0.0.1:8002/demo.html");await pg.wait_for_timeout(2500)
    f=[pg.frame_locator("#f%d"%i) for i in range(3)]
    await f[0].locator("#bSig").click();await pg.wait_for_timeout(2500)
    await f[1].locator("text=Sí").click();await f[2].locator(".op >> nth=1").click();await pg.wait_for_timeout(1500)
    n=await f[0].locator("#resp b").text_content()
    print("votos demo:",n); 
    if n!="2":fallos.append("demo no recibió 2 votos")
    g=await f[0].locator("#nGente").text_content();print("gente:",g)
    await f[0].locator("#bRev").click();await pg.wait_for_timeout(2000)
    await pg.screenshot(path="shots/demo.png")
    await br.close()
  print("fallos:",fallos);sys.exit(1 if fallos else 0)
asyncio.run(main())
