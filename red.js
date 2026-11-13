/*
 * red.js — Capa de conexión compartida por la pantalla y los celulares.
 * ======================================================================
 * Dos modos:
 *   • "firebase": usa la API REST de Firebase Realtime Database
 *     (sin librerías: fetch + EventSource, por eso pesa muy poco).
 *   • "local" (demo): si config.js no tiene FIREBASE_URL, o la dirección
 *     lleva ?demo, todo viaja entre pestañas/ventanas de la misma compu
 *     con BroadcastChannel y postMessage. Sirve para ensayar sin internet.
 *
 * Estructura en la base de datos:
 *   salas/AMOR26/estado            {q: -1..6, fase: "votando"|"revelado"}
 *   salas/AMOR26/gente/<id>         {a: "Jaguar 42"}       (quién entró)
 *   salas/AMOR26/votos/<q>/<id>     {v: respuesta, a: alias, t: hora}
 *
 * Pensado para mala señal:
 *   • Los votos se guardan primero en el celular y se reintentan cada 3 s
 *     hasta que llegan (y al volver la conexión).
 *   • Si la transmisión en vivo falla 3 veces, pasa a consultar cada 3 s.
 */
var Sala = (function () {
  "use strict";
  var C = window.CONFIG;
  var params = new URLSearchParams(location.search);

  function limpiarCodigo(s) { return String(s || "").toUpperCase().replace(/[^A-Z0-9]/g, ""); }
  var CODIGO = limpiarCodigo(C.CODIGO);
  var modo = C.FIREBASE_URL && !params.has("demo") ? "firebase" : "local";
  var BASE = String(C.FIREBASE_URL || "").replace(/\/+$/, "") + "/salas/" + CODIGO;
  var YO = params.get("yo") || (/^yo(\w+)$/.exec(window.name) || [])[1] || "";
  var PREF = "svt" + YO + "-"; // ?yo=2 (o name="yo2") separa celulares simulados; ?yo=vista = vista previa del expositor
  var ALIAS_VISTA = "Vista del expositor";

  // ---------- Almacenamiento seguro (algunos navegadores lo bloquean) ----------
  var mem = {};
  function leerLS(k) { try { var v = localStorage.getItem(PREF + k); return v == null ? mem[k] : v; } catch (e) { return mem[k]; } }
  function guardarLS(k, v) { mem[k] = v; try { localStorage.setItem(PREF + k, v); } catch (e) {} }
  function leerJSON(k, def) { try { return JSON.parse(leerLS(k)) || def; } catch (e) { return def; } }

  // ---------- Identidad anónima ----------
  var ANIMALES = ["Colibrí", "Jaguar", "Tucán", "Perezoso", "Danta", "Quetzal", "Mono", "Rana",
    "Lapa", "Pizote", "Manatí", "Tortuga", "Mariposa", "Búho", "Coyote", "Ocelote"];
  function miId() {
    var id = leerLS("id");
    if (!id) { id = "v" + Math.random().toString(36).slice(2, 10) + Date.now().toString(36).slice(-4); guardarLS("id", id); }
    return id;
  }
  function miAlias() {
    if (YO === "vista") return ALIAS_VISTA; // la vista previa no cuenta en los resultados
    var a = leerLS("alias");
    if (!a) { a = ANIMALES[Math.floor(Math.random() * ANIMALES.length)] + " " + (10 + Math.floor(Math.random() * 90)); guardarLS("alias", a); }
    return a;
  }

  // ---------- Avisos de conexión ----------
  var conectado = null, oyentesCon = [];
  function marcarConexion(ok) {
    if (ok === conectado) return;
    conectado = ok;
    oyentesCon.forEach(function (f) { f(ok); });
  }
  window.addEventListener("offline", function () { marcarConexion(false); });

  // ---------- Utilidad: aplicar un cambio en una ruta "/a/b" ----------
  function aplicar(raiz, ruta, dato) {
    var partes = String(ruta || "/").split("/").filter(Boolean);
    if (!partes.length) return dato;
    if (!raiz || typeof raiz !== "object") raiz = {};
    var o = raiz;
    for (var i = 0; i < partes.length - 1; i++) {
      if (!o[partes[i]] || typeof o[partes[i]] !== "object") o[partes[i]] = {};
      o = o[partes[i]];
    }
    var ult = partes[partes.length - 1];
    if (dato === null) delete o[ult]; else o[ult] = dato;
    return raiz;
  }

  // ---------- Modo Firebase ----------
  function escribir(sub, dato, metodo) {
    return fetch(BASE + sub + ".json", {
      method: metodo || "PUT",
      body: dato === undefined ? undefined : JSON.stringify(dato)
    }).then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      marcarConexion(true);
      return r;
    }).catch(function (e) { marcarConexion(false); throw e; });
  }
  function escuchar(sub, cb) {
    var url = BASE + sub + ".json", datos = null, fallos = 0, sondeo = null;
    function leer() {
      fetch(url, { cache: "no-store" }).then(function (r) { return r.json(); })
        .then(function (d) { datos = d; cb(datos); marcarConexion(true); })
        .catch(function () { marcarConexion(false); });
    }
    function iniciarSondeo() { if (!sondeo) { sondeo = setInterval(leer, 3000); leer(); } }
    if (!window.EventSource) return iniciarSondeo();
    var es = new EventSource(url);
    es.addEventListener("put", function (e) {
      var m = JSON.parse(e.data);
      datos = aplicar(datos, m.path, m.data);
      cb(datos); fallos = 0; marcarConexion(true);
      if (sondeo) { clearInterval(sondeo); sondeo = null; }
    });
    es.addEventListener("patch", function (e) {
      var m = JSON.parse(e.data), base = m.path.replace(/\/$/, "");
      Object.keys(m.data || {}).forEach(function (k) { datos = aplicar(datos, base + "/" + k, m.data[k]); });
      cb(datos); marcarConexion(true);
    });
    es.addEventListener("keep-alive", function () { marcarConexion(true); });
    es.onerror = function () { fallos++; marcarConexion(false); if (fallos >= 3) iniciarSondeo(); };
  }

  // ---------- Modo local (demo) ----------
  var bc = null, oyentesBus = [];
  if (modo === "local") {
    try { bc = new BroadcastChannel("svt-" + CODIGO); bc.onmessage = function (e) { recibir(e.data); }; } catch (e) {}
    window.addEventListener("message", function (e) { recibir(e.data); });
    setTimeout(function () { marcarConexion(true); }, 0);
  }
  function enviarBus(msg) {
    msg.__svt = 1;
    if (bc) try { bc.postMessage(msg); } catch (e) {}
    if (window.parent !== window) try { window.parent.postMessage(msg, "*"); } catch (e) {}
    // También a los marcos hijos (la vista previa del celular dentro de la pantalla)
    for (var i = 0; i < window.frames.length; i++) try { window.frames[i].postMessage(msg, "*"); } catch (e) {}
  }
  function recibir(msg) { if (msg && msg.__svt) oyentesBus.forEach(function (f) { f(msg); }); }

  // ---------- Votos con cola de reintento ----------
  var oyentesCola = [];
  function avisarCola() { var n = pendientes(); oyentesCola.forEach(function (f) { f(n); }); }
  function pendientes() { return Object.keys(leerJSON("cola", {})).length; }
  var enviando = {};
  function enviarCola() {
    var cola = leerJSON("cola", {});
    Object.keys(cola).forEach(function (q) {
      var voto = cola[q];
      if (enviando[q] === voto.t) return;
      enviando[q] = voto.t;
      var p = modo === "firebase"
        ? escribir("/votos/" + q + "/" + miId(), voto)
        : (enviarBus({ tipo: "voto", q: q, vid: miId(), val: voto }), Promise.resolve());
      p.then(function () {
        var c = leerJSON("cola", {});
        if (c[q] && c[q].t === voto.t) { delete c[q]; guardarLS("cola", JSON.stringify(c)); }
        avisarCola();
      }).catch(function () {}).then(function () { delete enviando[q]; });
    });
  }
  setInterval(enviarCola, 3000);
  window.addEventListener("online", enviarCola);

  function votar(q, valor) {
    var mis = leerJSON("mis", {});
    mis[q] = valor; guardarLS("mis", JSON.stringify(mis));
    var cola = leerJSON("cola", {});
    cola[q] = { v: valor, a: miAlias(), t: Date.now() };
    guardarLS("cola", JSON.stringify(cola));
    avisarCola(); enviarCola();
  }
  function misRespuestas() { return leerJSON("mis", {}); }
  function olvidar(q) { var mis = leerJSON("mis", {}); delete mis[q]; guardarLS("mis", JSON.stringify(mis)); }

  // ---------- API para los celulares ----------
  function votante(cbEstado) {
    var ultimo = null;
    function nuevoEstado(e) {
      e = e || { q: -1, fase: "votando" };
      var clave = e.q + "|" + e.fase + "|" + (e.t || 0);
      if (clave === ultimo) return;
      ultimo = clave;
      // Si la pantalla reinició los votos, se limpia lo guardado en el celular
      if (e.reinicio && e.reinicio !== leerLS("reinicio")) {
        guardarLS("reinicio", e.reinicio); guardarLS("mis", "{}"); guardarLS("cola", "{}");
      }
      cbEstado(e);
    }
    if (modo === "firebase") {
      var unir = function () {
        escribir("/gente/" + miId(), { a: miAlias() }).catch(function () { setTimeout(unir, 4000); });
      };
      unir();
      escuchar("/estado", nuevoEstado);
    } else {
      oyentesBus.push(function (m) { if (m.tipo === "estado") nuevoEstado(m.estado); });
      enviarBus({ tipo: "hola", vid: miId(), a: miAlias() });
    }
    enviarCola();
  }

  // ---------- API para la pantalla del expositor ----------
  function pantalla(cb) {
    if (modo === "firebase") {
      escuchar("", function (d) { cb(d || {}); });
      return {
        publicar: function (e) { return escribir("/estado", e); },
        reiniciar: function () { return Promise.all([escribir("/votos", undefined, "DELETE"), escribir("/gente", undefined, "DELETE")]); },
        simular: function (q, vid, val) { return escribir("/votos/" + q + "/" + vid, val); }
      };
    }
    var d = leerJSON("local", null) || { estado: { q: -1, fase: "votando" }, votos: {}, gente: {} };
    function guardar() { guardarLS("local", JSON.stringify(d)); cb(d); }
    function anunciar() { enviarBus({ tipo: "estado", estado: d.estado }); }
    oyentesBus.push(function (m) {
      if (m.tipo === "voto") { (d.votos[m.q] = d.votos[m.q] || {})[m.vid] = m.val; guardar(); }
      else if (m.tipo === "hola") { d.gente[m.vid] = { a: m.a }; guardar(); anunciar(); }
    });
    setInterval(anunciar, 2000);
    setTimeout(function () { cb(d); anunciar(); }, 0);
    return {
      publicar: function (e) { d.estado = e; guardar(); anunciar(); return Promise.resolve(); },
      reiniciar: function () { d.votos = {}; d.gente = {}; guardar(); return Promise.resolve(); },
      simular: function (q, vid, val) { (d.votos[q] = d.votos[q] || {})[vid] = val; guardar(); return Promise.resolve(); }
    };
  }

  return {
    modo: modo, CODIGO: CODIGO, ALIAS_VISTA: ALIAS_VISTA, limpiarCodigo: limpiarCodigo,
    miId: miId, miAlias: miAlias, votar: votar, misRespuestas: misRespuestas, olvidar: olvidar,
    pendientes: pendientes, alCambiarCola: function (f) { oyentesCola.push(f); },
    alCambiarConexion: function (f) { oyentesCon.push(f); if (conectado !== null) f(conectado); },
    votante: votante, pantalla: pantalla, aplicar: aplicar,
    leerLS: leerLS, guardarLS: guardarLS
  };
})();
