"""Prueba de extremo a extremo en modo Firebase (contra el servidor falso).
Pantalla + 3 celulares (2 ligeros, 1 completo), corte de red, mano alzada,
simulación de 30 votos por pregunta, revelado y reinicio."""
import asyncio, sys
from playwright.async_api import async_playwright

B = "http://127.0.0.1:8000/"
OUT = "/home/claude/tests/shots/"
errores = []
ok = []

def check(cond, msg):
    (ok if cond else errores).append(msg)
    print(("✔ " if cond else "✘ ") + msg)

async def num(page, sel):
    t = await page.text_content(sel)
    return int("".join(c for c in t if c.isdigit()) or 0)

async def main():
    async with async_playwright() as p:
        br = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        cp = await br.new_context(viewport={"width": 1600, "height": 900})
        pant = await cp.new_page()
        pant.on("pageerror", lambda e: errores.append("JS pantalla: " + str(e)))
        await pant.goto(B + "pantalla.html?prueba&sinpresentacion")
        await pant.wait_for_timeout(1200)
        # reinicio limpio
        await pant.click("#bReset"); await pant.click("#bReset"); await pant.wait_for_timeout(800)
        await pant.screenshot(path=OUT + "p0_portada.png")

        tels = []
        for i, pag in enumerate(["index.html", "index.html", "completa.html"]):
            c = await br.new_context(viewport={"width": 390, "height": 820}, is_mobile=True, has_touch=True)
            t = await c.new_page()
            t.on("pageerror", lambda e, i=i: errores.append(f"JS tel{i}: " + str(e)))
            await t.goto(B + pag + "?c=AMOR26")
            tels.append((c, t))
        await pant.wait_for_timeout(2500)
        check(await num(pant, "#nGente") == 3, "La pantalla cuenta 3 personas conectadas")
        await tels[0][1].screenshot(path=OUT + "t_ligera_espera.png")

        # Pregunta 1
        await pant.keyboard.press("ArrowRight"); await pant.wait_for_timeout(2000)
        await tels[0][1].click("text=Sí"); await tels[1][1].click("text=No"); await tels[2][1].click(".op >> nth=0")
        await pant.wait_for_timeout(2500)
        check(await num(pant, "#resp b") == 3, "Q1: llegan 3 votos desde celulares")
        await tels[2][1].screenshot(path=OUT + "t_completa_votado.png")
        # Mano alzada
        await pant.keyboard.press("m")
        for _ in range(3): await pant.keyboard.press("Digit2")
        await pant.wait_for_timeout(600)
        check(await num(pant, "#resp b") == 6, "Q1: mano alzada suma 3 votos (total 6)")
        await pant.keyboard.press("m")
        await pant.keyboard.press("Space"); await pant.wait_for_timeout(1500)
        await pant.screenshot(path=OUT + "p1_revelado.png")
        await tels[0][1].wait_for_timeout(1500)
        txt = await tels[0][1].text_content("main")
        check("78,6" in txt, "Q1: el celular ligero muestra el dato del TEC al revelar")
        await tels[0][1].screenshot(path=OUT + "t_ligera_revelado.png")

        # Pregunta 2 con corte de red en el celular 2
        await pant.keyboard.press("ArrowRight"); await pant.wait_for_timeout(2500)
        await tels[1][0].set_offline(True)
        await tels[0][1].fill("#w", "Ilusión"); await tels[0][1].click("#ok")
        await tels[2][1].click("[data-s=química]"); await tels[2][1].click("#ok")
        await tels[1][1].fill("#w", "nervios"); await tels[1][1].click("#ok")
        await pant.wait_for_timeout(2500)
        check(await num(pant, "#resp b") == 2, "Q2: con el celular 2 sin red llegan solo 2 palabras")
        t2 = await tels[1][1].text_content("main")
        check("Enviando" in t2, "Q2: el celular sin red muestra 'Enviando… se reintenta solo'")
        await tels[1][1].screenshot(path=OUT + "t_ligera_sin_red.png")
        await tels[1][0].set_offline(False)
        await pant.wait_for_timeout(6000)
        check(await num(pant, "#resp b") == 3, "Q2: al volver la red, el voto pendiente llega solo")

        # Simular 30 votos en cada pregunta y revelar
        for q in range(2, 7):
            if q > 2:
                await pant.keyboard.press("ArrowRight"); await pant.wait_for_timeout(1500)
            await pant.click("#bSim"); await pant.wait_for_timeout(5500)
            n = await num(pant, "#resp b")
            check(n >= 30, f"Q{q}: simulación registra {n} respuestas")
            await pant.screenshot(path=OUT + f"p{q}_votando.png")
            await pant.keyboard.press("Space"); await pant.wait_for_timeout(2000)
            await pant.screenshot(path=OUT + f"p{q}_revelado.png")
            if q in (5, 6):
                await tels[2][1].wait_for_timeout(1500)
                await tels[2][1].screenshot(path=OUT + f"t_completa_q{q}_revelado.png")
        # Celular completo en una pregunta de opciones antes de votar
        await pant.keyboard.press("Space"); await pant.wait_for_timeout(1500)
        await tels[2][1].screenshot(path=OUT + "t_completa_q6.png")
        await tels[0][1].screenshot(path=OUT + "t_ligera_q6.png")

        await pant.keyboard.press("ArrowRight"); await pant.wait_for_timeout(1500)
        await pant.screenshot(path=OUT + "p7_fin.png")

        # Reinicio
        await pant.click("#bReset"); await pant.click("#bReset"); await pant.wait_for_timeout(3000)
        check(await num(pant, "#nGente") == 0, "Reinicio: se vacía la sala")
        mis = await tels[0][1].evaluate("JSON.stringify(Sala.misRespuestas())")
        check(mis == "{}", "Reinicio: el celular olvida sus respuestas anteriores")
        await br.close()
    print(f"\n{len(ok)} pruebas OK, {len(errores)} fallos")
    for e in errores: print("  -", e)
    sys.exit(1 if errores else 0)

asyncio.run(main())
