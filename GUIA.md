# La sala vs. el TEC — Guía rápida

Interactivo en vivo para la exposición *“Factores psicológicos, biológicos y sociales que influyen en el enamoramiento”*.
El público responde desde el celular (QR **o** dirección + código) y la pantalla muestra los resultados en vivo, comparados con los 103 estudiantes del cuestionario.

---

## 1. Cómo funciona

```
 Celular del público                       Laptop del expositor (proyector)
 ──────────────────                        ──────────────────────────────
 Escanea QR  ─┐                            pantalla.html
 o escribe    ├─▶ index.html (ligera) ─┐    ▸ QR + dirección + código
 dirección +  │   completa.html (con   ├──▶ ▸ barras / nube / histograma en vivo
 código      ─┘   imágenes)            │    ▸ Espacio = revelar dato del TEC
                                       │    ▸ M = votos a mano alzada
                        Firebase Realtime Database
                        salas/AMOR26/{estado, gente, votos}
                                       │
             Si se cae la red ─────────┘─▶ el celular guarda el voto y lo reintenta solo;
                                          la pantalla sigue con mano alzada + datos TEC
```

| Archivo | Qué hace |
|---|---|
| `index.html` | **Versión ligera** del celular (la abre el QR). ~20 KB, sin imágenes. |
| `completa.html` | **Versión completa**: ilustraciones de la presentación, animaciones, confeti, vibración. ~200 KB. |
| `pantalla.html` | Lo que se proyecta. Controla las preguntas. |
| `demo.html` | Ensayo en una sola página (pantalla + 2 celulares) sin internet. |
| `config.js` | **Lo único que se edita**: dirección de Firebase, código, preguntas y datos del TEC. |
| `red.js` | Conexión (Firebase por REST, sin librerías) + cola de reintentos + modo demo. |
| `qr.js` | Generador de QR propio (funciona sin internet). |
| `img/` | Imágenes de la presentación comprimidas. |
| `database.rules.json`, `firebase.json` | Configuración para Firebase. |
| `pruebas/` | Pruebas automáticas (no se suben a internet). |

## 2. Las 6 preguntas

| # | Antes de la diapositiva | Pregunta | Se compara con |
|---|---|---|---|
| 1 | 2 | ¿Te has enamorado alguna vez? | 78,6% del TEC |
| 2 | 4 | El amor en una palabra (nube) | Voces del estudiantado (P16) |
| 3 | 11 (nueva diapositiva 10) | ¿Qué te pasa primero? | % «siempre o a veces» (P7) |
| 4 | 13 | ¿De la persona o de la versión que imaginas? | 65% / 40% (P8) |
| 5 | 15 (nueva diapositiva 14) | **Adivina** el % que la conoció en el campus | 57,3% + podio de los 3 más cercanos |
| 6 | 19 (nueva diapositiva 18) | ¿Qué pesa más? | 76,3 / 15,5 / 8,2 (P18) |

En la presentación (`Expo_interactiva.pptx`) se agregó una tarjeta con QR, dirección y código a las diapositivas 2, 4 y 13, y **3 diapositivas nuevas de votación** (10, 14 y 18), porque las diapositivas de resultados mostraban la respuesta antes de que el público votara.

---

## 3. Lo que ya está configurado

| Qué | Dónde |
|---|---|
| Firebase (plan gratuito **Spark**, sin costo) | proyecto `sala-vs-tec` · base `https://sala-vs-tec-default-rtdb.firebaseio.com` |
| Reglas de seguridad | `database.rules.json` (solo se puede escribir en `salas/…`; se probó que lo demás queda bloqueado) |
| Página pública (GitHub Pages, gratis) | **https://esclavotec.github.io/sala-vs-tec/** |
| Pantalla del expositor | https://esclavotec.github.io/sala-vs-tec/pantalla.html |

## 4. Si algún día cambias algo

Edita `config.js` en el repositorio `Esclavotec/sala-vs-tec` y GitHub Pages lo publica solo en uno o dos minutos. Si cambias la dirección, el QR de la pantalla se actualiza solo; el del .pptx hay que regenerarlo.

---

## 5. El día de la exposición

**Antes (en el aula):**
1. Abre `https://esclavotec.github.io/sala-vs-tec/pantalla.html` en la laptop. El punto verde arriba a la derecha indica que hay conexión.
2. Presiona **↺ Reiniciar votos** (dos clics) para borrar los ensayos.
3. Deja abiertas la presentación y la pantalla y cambia entre ellas con **Alt + Tab**.

**Durante:**

| Tecla | Acción |
|---|---|
| → / Av Pág | Siguiente pregunta (funciona con el control de diapositivas) |
| ← / Re Pág | Anterior |
| **Espacio** | Revelar / ocultar el dato del TEC |
| **M** | Panel de mano alzada |
| **1–5** | +1 a esa opción a mano alzada (Mayús + número = −1) |
| **V** | **Vista del público**: muestra en grande cómo se ve el celular (no cuenta en los resultados) |
| I | Portada con el QR grande |
| F | Pantalla completa |

- Al llegar a cada diapositiva de pregunta: Alt+Tab → ▶ → esperan unos 30 s → Espacio → Alt+Tab y siguen.
- **Gente sin datos/celular**: que levanten la mano, cuéntenlas con M + números. Se suman a las barras.
- **Palabras inapropiadas en la nube**: un clic sobre la palabra la oculta.
- **Si se cae el internet**: aparece un aviso amarillo. Los celulares guardan el voto y lo envían solos cuando vuelve la red; mientras tanto, usen la mano alzada. Los datos del TEC siempre se muestran porque vienen dentro de la página.

## 6. Ensayar sin internet

Abre `demo.html` (o la demo publicada): verás la pantalla y dos celulares simulados. Usa **🧪 Simular 30 votos** para llenar los gráficos. Para probar la versión real con Firebase y votos simulados, abre `pantalla.html?prueba`.

## 7. Pruebas realizadas

`pruebas/prueba_firebase.py` levanta un Firebase falso (`mock_firebase.py`) y controla la pantalla y 3 celulares con un navegador real:

| ✔ | Prueba |
|---|---|
| ✔ | La pantalla cuenta 3 personas conectadas |
| ✔ | Llegan los votos desde los celulares (ligera y completa) |
| ✔ | La mano alzada suma a las barras |
| ✔ | El celular muestra el dato del TEC al revelar |
| ✔ | Celular **sin red**: muestra “Enviando… se reintenta solo” y el voto **llega solo** al volver la red |
| ✔ | 30 votos simulados en cada una de las 6 preguntas (barras, nube, histograma, podio) |
| ✔ | Reiniciar vacía la sala y los celulares olvidan sus respuestas |
| ✔ | `prueba_demo.py`: el modo demo funciona sin Firebase |
| ✔ | Los QR (pantalla y .pptx) se leyeron con un lector de QR |

## 8. Privacidad

Todo es anónimo: cada celular recibe un nombre al azar (por ejemplo “Jaguar 42”) y no se pide nombre ni correo. Después de la exposición puedes borrar la base de datos desde la consola de Firebase.
