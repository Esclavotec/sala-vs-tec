"""Recrea las animaciones del PowerPoint para la web.

Lee de cada diapositiva su secuencia de animaciones de entrada (desvanecer,
barrido), genera una imagen por paso (la diapositiva con los elementos que aún
no aparecen ocultos) y escribe diapositivas/animaciones.js con los tiempos.

Uso: python3 animaciones.py Expo_interactiva.pptx /ruta/sala-vs-tec/diapositivas
"""
import sys, os, copy, json, subprocess, tempfile
from lxml import etree
from pptx import Presentation
from PIL import Image, ImageChops

P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
ent, salida = sys.argv[1], sys.argv[2]


def leer_animaciones(slide):
    """Devuelve una lista de grupos [{disparo: 'auto'|'clic', pasos:[{spid,t,d,ef}]}]."""
    timing = slide._element.find(P + "timing")
    if timing is None:
        return []
    grupos = []
    for ctn in timing.iter(P + "cTn"):
        if ctn.get("presetClass") != "entr":
            continue
        tg = ctn.find(".//" + P + "spTgt")
        if tg is None:
            continue
        # retraso: suma de los retrasos numéricos de los <p:par> que lo contienen
        t = 0
        for anc in ctn.iterancestors(P + "par"):
            c = anc.find(P + "cTn/" + P + "stCondLst/" + P + "cond")
            if c is not None and (c.get("delay") or "").isdigit():
                t += int(c.get("delay"))
        durs = [int(e.get("dur")) for e in ctn.iter(P + "cTn") if (e.get("dur") or "").isdigit() and int(e.get("dur")) > 1]
        filtros = [e.get("filter") or "" for e in ctn.iter(P + "animEffect")]
        ef = "barrido" if any("wipe" in f for f in filtros) or ctn.get("presetID") == "22" else "desvanecer"
        paso = {"spid": tg.get("spid"), "t": t, "d": max(durs) if durs else 500, "ef": ef}
        tipo = ctn.get("nodeType")
        if tipo == "clickEffect" or not grupos:
            grupos.append({"disparo": "clic" if tipo == "clickEffect" else "auto", "pasos": []})
        grupos[-1]["pasos"].append(paso)
    return grupos


prs = Presentation(ent)
anim = {}
for n, sl in enumerate(prs.slides, 1):
    g = leer_animaciones(sl)
    if g:
        anim[n] = g
print("Diapositivas con animación:", {n: [(x["disparo"], len(x["pasos"])) for x in g] for n, g in anim.items()})

maxpasos = max(sum(len(x["pasos"]) for x in g) for g in anim.values())
tmp = tempfile.mkdtemp()
# Variante f: en cada diapositiva animada se ocultan los elementos del paso f en adelante
for f in range(maxpasos + 1):   # la última variante = estado final, del mismo renderizado
    prs2 = Presentation(ent)
    for n, g in anim.items():
        orden = [p["spid"] for x in g for p in x["pasos"]]
        if f >= len(orden):
            continue
        ocultar = set(orden[f:])
        for el in prs2.slides[n - 1]._element.iter(P + "cNvPr"):
            if el.get("id") in ocultar:
                el.set("hidden", "1")
    ruta = os.path.join(tmp, f"v{f}.pptx")
    prs2.save(ruta)
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", tmp, ruta], check=True, capture_output=True, timeout=300)
    for n, g in anim.items():
        if f <= sum(len(x["pasos"]) for x in g):
            png = os.path.join(tmp, f"v{f}-{n}")
            subprocess.run(["pdftoppm", "-png", "-f", str(n), "-l", str(n), "-scale-to-x", "1920", "-scale-to-y", "1080", "-singlefile",
                            os.path.join(tmp, f"v{f}.pdf"), png], check=True)
    print("variante", f, "lista")

# Imágenes por paso y caja (en %) de lo que cambia en cada paso
datos = {}
for n, g in anim.items():
    total = sum(len(x["pasos"]) for x in g)
    imgs = [Image.open(os.path.join(tmp, f"v{f}-{n}.png")).convert("RGB") for f in range(total + 1)]
    imgs[-1].save(os.path.join(salida, f"{n:02d}.webp"), "WEBP", quality=82, method=6)  # estado final
    for f, im in enumerate(imgs[:-1]):
        im.save(os.path.join(salida, f"{n:02d}-{f}.webp"), "WEBP", quality=82, method=6)
    k = 0
    for x in g:
        for p in x["pasos"]:
            caja = ImageChops.difference(imgs[k], imgs[k + 1]).convert("L").point(lambda v: 255 if v > 12 else 0).getbbox()
            if not caja:
                caja = (0, 0, 1920, 1080)
            p["caja"] = [round(caja[0] / 19.2, 2), round(caja[1] / 10.8, 2), round(caja[2] / 19.2, 2), round(caja[3] / 10.8, 2)]
            p["img"] = f"{n:02d}-{k + 1}.webp" if k + 1 < total else f"{n:02d}.webp"
            del p["spid"]
            k += 1
    datos[n] = {"inicio": f"{n:02d}-0.webp", "grupos": g}

with open(os.path.join(salida, "animaciones.js"), "w") as fh:
    fh.write("/* Generado por animaciones.py desde el PowerPoint: secuencia de animaciones por diapositiva.\n"
             "   inicio = imagen sin los elementos animados; cada paso muestra su imagen dentro de 'caja' (en %)\n"
             "   con 'desvanecer' o 'barrido' (de izquierda a derecha), t = retraso en ms, d = duración en ms.\n"
             "   disparo 'auto' = al llegar a la diapositiva; 'clic' = con la flecha siguiente. */\n")
    fh.write("var ANIMACIONES = " + json.dumps(datos, ensure_ascii=False, indent=1) + ";\n")
print(json.dumps({n: [(x["disparo"], [(p["t"], p["d"], p["ef"], p["caja"]) for p in x["pasos"]]) for x in d["grupos"]] for n, d in datos.items()}, indent=0)[:2500])
