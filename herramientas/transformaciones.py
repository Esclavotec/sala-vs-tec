"""Recrea para la web la transición "Transformación" (Morph) del PowerPoint.

Para cada diapositiva con Transformación y su diapositiva anterior:
  - saca cada elemento "!!nombre" por separado, con fondo transparente, y su posición;
  - genera el fondo de cada diapositiva SIN esos elementos (final y, si tiene
    animaciones, también sin los elementos animados = estado inicial);
  - escribe diapositivas/transformaciones.js con los pares, tiempos e imágenes.

Uso: python3 transformaciones.py Expo_interactiva.pptx /ruta/sala-vs-tec/diapositivas
(ejecutar después de animaciones.py)
"""
import sys, os, re, json, subprocess, tempfile, copy
from lxml import etree
from pptx import Presentation
from PIL import Image

P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
ent, salida = sys.argv[1], sys.argv[2]
morf = os.path.join(salida, "morf")
os.makedirs(morf, exist_ok=True)
tmp = tempfile.mkdtemp()

prs = Presentation(ent)
N = len(prs.slides)


def es_morph(sl):
    return "p159:morph" in etree.tostring(sl._element).decode()


def dur_morph(sl):
    m = re.search(r'p14:dur="(\d+)"[^>]*>\s*<p159:morph', etree.tostring(sl._element).decode())
    return int(m.group(1)) if m else 1200


def nombres(sl):
    return {sh.name[2:]: sh.shape_id for sh in sl.shapes if sh.name.startswith("!!")}


def animados(sl):
    t = sl._element.find(P + "timing")
    return {tg.get("spid") for tg in t.iter(P + "spTgt")} if t is not None else set()


pares = {}
for n in range(2, N + 1):
    sb, sa = prs.slides[n - 1], prs.slides[n - 2]
    if es_morph(sb) and (set(nombres(sa)) | set(nombres(sb))):
        pares[n] = {"desde": n - 1, "dur": dur_morph(sb)}
todos = sorted({k for n in pares for k in list(nombres(prs.slides[n - 1])) + list(nombres(prs.slides[n - 2]))})
print("Pares con Transformación:", sorted(pares), "| elementos:", todos)


def render(nombre_var, modificar, paginas, transparente=False):
    """Guarda una variante modificada, la convierte a PDF y devuelve {página: PNG}."""
    p2 = Presentation(ent)
    for i, sl in enumerate(p2.slides, 1):
        modificar(i, sl)
    ruta = os.path.join(tmp, nombre_var + ".pptx")
    p2.save(ruta)
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", tmp, ruta], check=True, capture_output=True, timeout=300)
    out = {}
    for pg in paginas:
        base = os.path.join(tmp, f"{nombre_var}-{pg}")
        cmd = ["pdftocairo", "-png", "-singlefile", "-f", str(pg), "-l", str(pg), "-scale-to-x", "1920", "-scale-to-y", "1080"]
        if transparente:
            cmd.append("-transp")
        subprocess.run(cmd + [os.path.join(tmp, nombre_var + ".pdf"), base], check=True)
        out[pg] = base + ".png"
    print("  variante", nombre_var, "lista")
    return out


def ocultar(sl, ids):
    for el in sl._element.find(P + "cSld").iter(P + "cNvPr"):
        if el.get("id") in ids:
            el.set("hidden", "1")


paginas = sorted({n for n in pares} | {pares[n]["desde"] for n in pares})

# 1) cada elemento solo. LibreOffice siempre pinta el fondo de la página, así que se
#    renderiza sobre blanco y sobre negro y se calcula la transparencia exacta:
#    alfa = 1 - (blanco - negro), color = negro / alfa.
import numpy as np
recortes = {}
for nom in todos:
  imgs = {}
  for fondo in ("FFFFFF", "000000"):
    def solo(i, sl, nom=nom, fondo=fondo):
        keep = {str(v) for k, v in nombres(sl).items() if k == nom}
        ocultar(sl, {el.get("id") for el in sl._element.find(P + "cSld").iter(P + "cNvPr")} - keep)
        cs = sl._element.find(P + "cSld")
        bg = cs.find(P + "bg")
        if bg is not None:
            cs.remove(bg)
        cs.insert(0, etree.fromstring('<p:bg xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
                                      'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
                                      '<p:bgPr><a:solidFill><a:srgbClr val="%s"/></a:solidFill><a:effectLst/></p:bgPr></p:bg>' % fondo))
        sl._element.set("showMasterSp", "0")
    pags = [pg for pg in paginas if nom in nombres(prs.slides[pg - 1])]
    imgs[fondo] = render("solo_%s_%s" % (nom, fondo), solo, pags)
  for pg in imgs["FFFFFF"]:
        w = np.asarray(Image.open(imgs["FFFFFF"][pg]).convert("RGB")).astype(float)
        k = np.asarray(Image.open(imgs["000000"][pg]).convert("RGB")).astype(float)
        alfa = np.clip(1 - (w - k).mean(axis=2) / 255.0, 0, 1)
        color = np.where(alfa[..., None] > 0.004, np.clip(k / np.maximum(alfa[..., None], 1e-3), 0, 255), 0)
        alfa[:4, :] = 0; alfa[-4:, :] = 0; alfa[:, :4] = 0; alfa[:, -4:] = 0   # borde de página del PDF
        rgba = np.dstack([color, alfa * 255]).astype(np.uint8)
        im = Image.fromarray(rgba, "RGBA")
        caja = im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
        if not caja:
            continue
        archivo = f"{pg:02d}-{nom}.webp"
        im.crop(caja).save(os.path.join(morf, archivo), "WEBP", quality=88, method=6)
        recortes[(pg, nom)] = {"img": "morf/" + archivo,
                               "rect": [round(caja[0] / 19.2, 3), round(caja[1] / 10.8, 3),
                                        round((caja[2] - caja[0]) / 19.2, 3), round((caja[3] - caja[1]) / 10.8, 3)]}

# 2) fondos sin los elementos que se transforman (estado final y estado inicial)
def sin_morf(i, sl):
    ocultar(sl, {str(v) for v in nombres(sl).values()})


def sin_morf_inicio(i, sl):
    ocultar(sl, {str(v) for v in nombres(sl).values()} | animados(sl))


fin = render("sin", sin_morf, paginas)
con_anim = [pg for pg in paginas if animados(prs.slides[pg - 1])]
ini = render("sin0", sin_morf_inicio, con_anim) if con_anim else {}
for pg, png in fin.items():
    Image.open(png).convert("RGB").save(os.path.join(morf, f"{pg:02d}-sin.webp"), "WEBP", quality=82, method=6)
for pg, png in ini.items():
    Image.open(png).convert("RGB").save(os.path.join(morf, f"{pg:02d}-sin0.webp"), "WEBP", quality=82, method=6)

# 3) datos para la web
datos = {}
for n, info in pares.items():
    a, b = info["desde"], n
    elementos = []
    for nom in sorted(set(nombres(prs.slides[a - 1])) | set(nombres(prs.slides[b - 1]))):
        ea, eb = recortes.get((a, nom)), recortes.get((b, nom))
        if ea or eb:
            elementos.append({"nombre": nom, "a": ea, "b": eb})
    datos[n] = {"desde": a, "dur": info["dur"],
                "fondoA": f"morf/{a:02d}-sin.webp",
                "fondoB": f"morf/{b:02d}-sin0.webp" if b in ini else f"morf/{b:02d}-sin.webp",
                "elementos": elementos}

with open(os.path.join(salida, "transformaciones.js"), "w") as fh:
    fh.write("/* Generado por transformaciones.py: transición Transformación (Morph) del PowerPoint.\n"
             "   Para llegar a la diapositiva N desde 'desde': el fondo A se desvanece, aparece el fondo B\n"
             "   y cada elemento viaja de su rect en A a su rect en B (en %), fundiendo su imagen. */\n")
    fh.write("var TRANSFORMACIONES = " + json.dumps(datos, ensure_ascii=False, indent=1) + ";\n")
for n, d in datos.items():
    print(n, "←", d["desde"], d["dur"], "ms", [(e["nombre"], bool(e["a"]), bool(e["b"])) for e in d["elementos"]])
