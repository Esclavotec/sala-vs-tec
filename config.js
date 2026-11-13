/*
 * config.js — LO ÚNICO QUE HAY QUE EDITAR
 * ======================================================================
 * 1) FIREBASE_URL: la dirección de tu Realtime Database
 *    (Firebase → Realtime Database → arriba aparece algo como
 *     https://sala-vs-tec-default-rtdb.firebaseio.com). Pégala tal cual.
 *    Si la dejas vacía, todo funciona en "modo demo" (solo en esta compu).
 * 2) CODIGO: el código que escribe el público. Solo letras y números.
 * 3) DIRECCION: lo que se muestra en pantalla para que la gente lo escriba.
 *    Si la dejas vacía se usa la dirección real de la página.
 *
 * Datos del TEC: salen del "Cuestionario de Enamoramiento Universitario"
 * (n = 103). Se calcularon desde el Excel y coinciden con las diapositivas.
 */
var CONFIG = {
  FIREBASE_URL: "https://sala-vs-tec-default-rtdb.firebaseio.com",
  CODIGO: "AMOR26",
  DIRECCION: "esclavotec.github.io/sala-vs-tec",

  PREGUNTAS: [
    {
      id: "q1", tipo: "opciones", diapositiva: 2, img: "pareja",
      titulo: "¿Te has enamorado alguna vez?",
      opciones: ["Sí", "No"],
      tec: [78.6, 21.4],
      tecNota: "TEC: se enamoró en los últimos 12 meses (81 de 103)"
    },
    {
      id: "q2", tipo: "palabra", diapositiva: 4, img: "cabeza",
      titulo: "En una palabra: ¿qué es para ti el amor?",
      sugerencias: ["ilusión", "nervios", "química", "decisión", "paz", "costumbre"],
      voces: [
        "“Me genera paz… el tiempo con él representa un respiro de mi estrés habitual.”",
        "“Fue paulatino enamorarme de ella; al principio solo era amistad.”",
        "“La semana de exámenes en la biblioteca.”"
      ],
      tecNota: "Voces del estudiantado TEC · respuestas abiertas P16"
    },
    {
      id: "q3", tipo: "opciones", diapositiva: 10, img: "corazon",
      titulo: "Cuando ves a esa persona… ¿qué te pasa primero?",
      opciones: ["Corazón acelerado", "Mariposas en el estómago", "Manos sudadas / nervios", "Me cuesta dormir", "Cambia mi apetito"],
      tec: [68.0, 52.9, 37.9, 26.7, 24.3],
      tecNota: "TEC: % que lo siente «siempre» o «a veces» (P7, n = 101 a 103)"
    },
    {
      id: "q4", tipo: "opciones", diapositiva: 12, img: "flores",
      titulo: "¿Te enamoras de la persona… o de la versión que imaginas?",
      opciones: ["De la persona real", "De la versión que imagino", "Un poco de las dos"],
      tec: null,
      tecNota: "TEC: el 65% siempre se imagina compartiendo más tiempo y el 40% se fija siempre más en cualidades que en defectos"
    },
    {
      id: "q5", tipo: "numero", diapositiva: 13, img: "espejo",
      titulo: "Adivina: ¿qué % del TEC conoció a esa persona en el campus?",
      respuesta: 57.3,
      tecNota: "TEC: 57,3% la conoció en clases, grupos de estudio o actividades de la U (59 de 103)"
    },
    {
      id: "q6", tipo: "opciones", diapositiva: 16, img: "reflejo",
      titulo: "¿Qué pesa más en tu manera de enamorarte?",
      opciones: ["Lo que siento en el cuerpo", "Lo que pienso y he vivido", "Mi entorno social"],
      tec: [15.5, 76.3, 8.2],
      tecNota: "TEC: factor puesto en primer lugar (P18, n = 97)"
    }
  ]
};
