"""Agrega a la presentación: tarjeta QR + dirección + código en las diapositivas
de pregunta (2, 4, 12) e inserta diapositivas de votación antes de 10, 13 y 16
(para que el público vote ANTES de ver el dato del TEC).
Uso: python3 pptx_qr.py <entrada.pptx> <salida.pptx> <direccion> <codigo>"""
import sys, json, subprocess, copy
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from PIL import Image

ent, sal, DIR, COD = sys.argv[1:5]
ROJO, OSC, CREMA, DUR, BLANCO = RGBColor(0x8A,0x0B,0x14), RGBColor(0x4D,0x05,0x09), RGBColor(0xEC,0xE8,0xE3), RGBColor(0xE9,0xAA,0x8C), RGBColor(255,255,255)

subprocess.run(["node", "qr_png.js", f"https://{DIR}/?c={COD}", "qr.json"], check=True)
M = json.load(open("qr.json")); n = len(M); esc = 24; mg = 2
img = Image.new("RGB", ((n+2*mg)*esc,)*2, "white"); px = img.load()
for y in range(n):
    for x in range(n):
        if M[y][x]:
            for dy in range(esc):
                for dx in range(esc): px[(x+mg)*esc+dx, (y+mg)*esc+dy] = (0x4D,0x05,0x09)
img.save("qr.png")

def texto(sl, x, y, w, h, t, size, color, bold=True, align=PP_ALIGN.LEFT, spacing=None):
    tb = sl.shapes.add_textbox(x, y, w, h); tf = tb.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    lines = t if isinstance(t, list) else [t]
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p.alignment = align
        for seg in (ln if isinstance(ln, list) else [(ln, size, color, bold)]):
            r = p.add_run(); r.text = seg[0]; r.font.size = Pt(seg[1]); r.font.color.rgb = seg[2]; r.font.bold = seg[3]; r.font.name = "Arial"
            if spacing: r.font._element.set("spc", str(spacing))
    return tb

def tarjeta(sl, x, y, oscuro=False):
    """Tarjeta pequeña: QR + 'Respondan en vivo' + dirección + código."""
    w, h = Inches(4.6), Inches(1.25)
    r = sl.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    r.adjustments[0] = 0.12; r.fill.solid(); r.fill.fore_color.rgb = BLANCO; r.line.fill.background(); r.shadow.inherit = False
    sl.shapes.add_picture("qr.png", x + Inches(0.12), y + Inches(0.12), Inches(1.01), Inches(1.01))
    texto(sl, x+Inches(1.28), y+Inches(0.12), Inches(3.2), Inches(0.28), "RESPONDAN EN VIVO", 9, ROJO, spacing=150)
    texto(sl, x+Inches(1.28), y+Inches(0.42), Inches(3.2), Inches(0.34), DIR, 15, OSC)
    texto(sl, x+Inches(1.28), y+Inches(0.80), Inches(3.2), Inches(0.33), [[("Código  ", 11, OSC, False), (COD, 17, ROJO, True)]], 11, ROJO, spacing=None)

def poner_nota(sl, t):
    """Nota del orador (si la plantilla de notas lo permite)."""
    tf = sl.notes_slide.notes_text_frame
    if tf is not None: tf.text = t

prs = Presentation(ent)
W, H = prs.slide_width, prs.slide_height
s = prs.slides
# Quitar la indicación "Levanten la mano…" de la diapositiva 2 (ahora se responde en el celular)
for sh in list(s[1].shapes):
    if sh.has_text_frame and sh.text_frame.text.strip().startswith("Levanten la mano"):
        sh._element.getparent().remove(sh._element)
# Tarjetas en las diapositivas que ya son preguntas
tarjeta(s[1], Inches(0.75), Inches(6.0))           # 2  ¿Quién se ha enamorado?
tarjeta(s[3], Inches(8.35), Inches(6.1))           # 4  En una palabra
tarjeta(s[11], Inches(0.72), Inches(6.05))         # 12 ¿De la persona o de la versión?
NOTA_PREG = "EN VIVO: cambia a la ventana de la pantalla (Alt+Tab), dale ▶ a la pregunta {n}, espera las respuestas y presiona Espacio para revelar el dato del TEC. Vuelve a la presentación con Alt+Tab."
for idx, n in [(1, 1), (3, 2), (11, 4)]:
    poner_nota(s[idx], NOTA_PREG.format(n=n))

# Diapositivas de votación nuevas (antes de 10, 13 y 16)
nuevas = [
    (9,  3, "Cuando ves a esa persona…\n¿qué te pasa primero?", "Corazón acelerado · mariposas · manos sudadas · me cuesta dormir · cambia mi apetito", "corazon"),
    (12, 5, "Adivina: ¿qué % del TEC conoció a esa persona en el campus?", "Pon tu apuesta del 0 al 100. Quien se acerque más gana el podio.", "espejo"),
    (15, 6, "¿Qué pesa más en tu manera de enamorarte?", "Lo que siento en el cuerpo · lo que pienso y he vivido · mi entorno social", "reflejo"),
]
blank = prs.slide_layouts[6] if len(prs.slide_layouts) > 6 else prs.slide_layouts[-1]
ids = prs.slides._sldIdLst
creadas = []
for pos, q, titulo, sub, img_nom in nuevas:
    sl = prs.slides.add_slide(blank)
    for ph in list(sl.placeholders): ph._element.getparent().remove(ph._element)
    bg = sl.background.fill; bg.solid(); bg.fore_color.rgb = CREMA
    banda = sl.shapes.add_shape(MSO_SHAPE.RECTANGLE, W - Inches(5.3), 0, Inches(5.3), H)
    banda.fill.solid(); banda.fill.fore_color.rgb = ROJO; banda.line.fill.background()
    pill = sl.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.75), Inches(0.7), Inches(3.2), Inches(0.42))
    pill.adjustments[0] = 0.5; pill.fill.solid(); pill.fill.fore_color.rgb = ROJO; pill.line.fill.background()
    pt = pill.text_frame; pt.text = f"EN VIVO · PREGUNTA {q} DE 6"; r = pt.paragraphs[0].runs[0]
    r.font.size = Pt(11); r.font.bold = True; r.font.color.rgb = BLANCO; r.font.name = "Arial"; pt.paragraphs[0].alignment = PP_ALIGN.CENTER
    texto(sl, Inches(0.75), Inches(1.5), Inches(6.9), Inches(2.6), titulo.split("\n"), 36, ROJO)
    texto(sl, Inches(0.75), Inches(4.25), Inches(6.6), Inches(0.9), sub, 15, OSC, bold=False)
    texto(sl, Inches(0.75), Inches(5.4), Inches(6.6), Inches(0.9), "Respondan antes de ver el dato del TEC.", 13, RGBColor(0x7A,0x5A,0x5C), bold=False)
    # QR grande en la banda roja
    caja = sl.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, W - Inches(4.55), Inches(0.75), Inches(3.8), Inches(3.8))
    caja.adjustments[0] = 0.06; caja.fill.solid(); caja.fill.fore_color.rgb = BLANCO; caja.line.fill.background()
    sl.shapes.add_picture("qr.png", W - Inches(4.4), Inches(0.9), Inches(3.5), Inches(3.5))
    texto(sl, W - Inches(5.0), Inches(4.75), Inches(4.7), Inches(0.35), "ESCANEEN O ENTREN A", 11, DUR, spacing=150, align=PP_ALIGN.CENTER)
    texto(sl, W - Inches(5.0), Inches(5.1), Inches(4.7), Inches(0.55), DIR, 22, BLANCO, align=PP_ALIGN.CENTER)
    texto(sl, W - Inches(5.0), Inches(5.75), Inches(4.7), Inches(0.35), "Y ESCRIBAN EL CÓDIGO", 11, DUR, spacing=150, align=PP_ALIGN.CENTER)
    cc = sl.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, W - Inches(4.15), Inches(6.15), Inches(3.0), Inches(0.75))
    cc.adjustments[0] = 0.2; cc.fill.solid(); cc.fill.fore_color.rgb = BLANCO; cc.line.fill.background()
    ct = cc.text_frame; ct.text = COD; r = ct.paragraphs[0].runs[0]; r.font.size = Pt(30); r.font.bold = True; r.font.color.rgb = ROJO; r.font.name = "Arial"
    r.font._element.set("spc", "600"); ct.paragraphs[0].alignment = PP_ALIGN.CENTER
    poner_nota(sl, NOTA_PREG.format(n=q) + " La diapositiva siguiente muestra el dato del TEC: pásala después de revelar.")
    creadas.append((pos, ids[-1]))
# Reordenar: insertar cada nueva diapositiva antes de la original (de atrás hacia adelante)
for pos, el in sorted(creadas, key=lambda t: -t[0]):
    ids.remove(el); ids.insert(pos, el)
prs.save(sal)
print("ok", len(prs.slides), "diapositivas")
