/*
 * qr.js — Generador de códigos QR sin dependencias (sin internet).
 * ------------------------------------------------------------------
 * Basado en el algoritmo estándar ISO/IEC 18004 (modo byte, versiones 1–10,
 * corrección de errores L o M). Sirve tanto en el navegador como en Node.
 *
 *   QR.matrix("https://ejemplo.web.app/?c=AMOR26")  -> matriz de booleanos
 *   QR.svg(texto, {margin:4, dark:"#000", light:"#fff"}) -> texto SVG
 *
 * Se escribió aquí mismo para que la pantalla genere el QR aunque el aula
 * no tenga buena conexión (no depende de ninguna librería externa).
 */
(function (root) {
  "use strict";
  // Tablas oficiales (índice = versión). Solo L (1) y M (0) hasta la versión 10.
  var ECC = {
    L: [-1, 7, 10, 15, 20, 26, 18, 20, 24, 30, 18],
    M: [-1, 10, 16, 26, 18, 24, 16, 18, 22, 22, 26]
  };
  var BLOCKS = {
    L: [-1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 4],
    M: [-1, 1, 1, 1, 2, 2, 4, 4, 4, 5, 5]
  };
  var FORMAT = { L: 1, M: 0 };

  function rawModules(v) {
    var r = (16 * v + 128) * v + 64;
    if (v >= 2) {
      var n = Math.floor(v / 7) + 2;
      r -= (25 * n - 10) * n - 55;
      if (v >= 7) r -= 36;
    }
    return r;
  }
  function dataCodewords(v, e) {
    return Math.floor(rawModules(v) / 8) - ECC[e][v] * BLOCKS[e][v];
  }
  function utf8(s) {
    return Array.from(unescape(encodeURIComponent(s))).map(function (c) { return c.charCodeAt(0); });
  }
  function gfMul(x, y) {
    var z = 0;
    for (var i = 7; i >= 0; i--) {
      z = (z << 1) ^ ((z >>> 7) * 0x11d);
      z ^= ((y >>> i) & 1) * x;
    }
    return z & 0xff;
  }
  function rsDivisor(deg) {
    var r = [];
    for (var i = 0; i < deg - 1; i++) r.push(0);
    r.push(1);
    var root = 1;
    for (i = 0; i < deg; i++) {
      for (var j = 0; j < r.length; j++) {
        r[j] = gfMul(r[j], root);
        if (j + 1 < r.length) r[j] ^= r[j + 1];
      }
      root = gfMul(root, 2);
    }
    return r;
  }
  function rsRemainder(data, div) {
    var r = div.map(function () { return 0; });
    data.forEach(function (b) {
      var f = b ^ r.shift();
      r.push(0);
      div.forEach(function (c, i) { r[i] ^= gfMul(c, f); });
    });
    return r;
  }
  function bit(x, i) { return ((x >>> i) & 1) !== 0; }

  function matrix(text, ecl) {
    var e = ecl || "M";
    var bytes = utf8(text);
    var ver = 0;
    for (var v = 1; v <= 10; v++) {
      var cc = v <= 9 ? 8 : 16;
      if (4 + cc + bytes.length * 8 <= dataCodewords(v, e) * 8) { ver = v; break; }
    }
    if (!ver) {
      if (e === "M") return matrix(text, "L");
      throw new Error("Texto demasiado largo para el QR");
    }
    // --- Bits de datos ---
    var bits = [];
    function put(val, len) { for (var i = len - 1; i >= 0; i--) bits.push((val >>> i) & 1); }
    put(4, 4);
    put(bytes.length, ver <= 9 ? 8 : 16);
    bytes.forEach(function (b) { put(b, 8); });
    var cap = dataCodewords(ver, e) * 8;
    put(0, Math.min(4, cap - bits.length));
    put(0, (8 - (bits.length % 8)) % 8);
    for (var pad = 0xec; bits.length < cap; pad ^= 0xec ^ 0x11) put(pad, 8);
    var data = [];
    for (var i = 0; i < bits.length; i += 8) {
      var b = 0;
      for (var k = 0; k < 8; k++) b = (b << 1) | bits[i + k];
      data.push(b);
    }
    // --- Corrección de errores + intercalado ---
    var nb = BLOCKS[e][ver], el = ECC[e][ver], raw = Math.floor(rawModules(ver) / 8);
    var nShort = nb - (raw % nb), shortLen = Math.floor(raw / nb);
    var div = rsDivisor(el), blocks = [], p = 0;
    for (i = 0; i < nb; i++) {
      var dat = data.slice(p, p + shortLen - el + (i < nShort ? 0 : 1));
      p += dat.length;
      var ecc = rsRemainder(dat, div);
      if (i < nShort) dat.push(0);
      blocks.push(dat.concat(ecc));
    }
    var cw = [];
    for (i = 0; i < blocks[0].length; i++)
      for (var j = 0; j < blocks.length; j++)
        if (i !== shortLen - el || j >= nShort) cw.push(blocks[j][i]);

    // --- Matriz ---
    var size = ver * 4 + 17, M = [], F = [];
    for (i = 0; i < size; i++) {
      M.push(new Array(size).fill(false));
      F.push(new Array(size).fill(false));
    }
    function setF(x, y, d) { M[y][x] = d; F[y][x] = true; }
    for (i = 0; i < size; i++) { setF(6, i, i % 2 === 0); setF(i, 6, i % 2 === 0); }
    function finder(x, y) {
      for (var dy = -4; dy <= 4; dy++) for (var dx = -4; dx <= 4; dx++) {
        var d = Math.max(Math.abs(dx), Math.abs(dy)), xx = x + dx, yy = y + dy;
        if (xx >= 0 && xx < size && yy >= 0 && yy < size) setF(xx, yy, d !== 2 && d !== 4);
      }
    }
    finder(3, 3); finder(size - 4, 3); finder(3, size - 4);
    var al = [];
    if (ver > 1) {
      var na = Math.floor(ver / 7) + 2;
      var step = Math.ceil((ver * 4 + 4) / (na * 2 - 2)) * 2;
      al = [6];
      for (var pos = size - 7; al.length < na; pos -= step) al.splice(1, 0, pos);
    }
    for (i = 0; i < al.length; i++) for (j = 0; j < al.length; j++) {
      if ((i === 0 && j === 0) || (i === 0 && j === al.length - 1) || (i === al.length - 1 && j === 0)) continue;
      for (var dy2 = -2; dy2 <= 2; dy2++) for (var dx2 = -2; dx2 <= 2; dx2++)
        setF(al[i] + dx2, al[j] + dy2, Math.max(Math.abs(dx2), Math.abs(dy2)) !== 1);
    }
    function format(mask) {
      var d = (FORMAT[e] << 3) | mask, r = d;
      for (var i = 0; i < 10; i++) r = (r << 1) ^ ((r >>> 9) * 0x537);
      var bt = ((d << 10) | r) ^ 0x5412;
      for (i = 0; i <= 5; i++) setF(8, i, bit(bt, i));
      setF(8, 7, bit(bt, 6)); setF(8, 8, bit(bt, 7)); setF(7, 8, bit(bt, 8));
      for (i = 9; i < 15; i++) setF(14 - i, 8, bit(bt, i));
      for (i = 0; i < 8; i++) setF(size - 1 - i, 8, bit(bt, i));
      for (i = 8; i < 15; i++) setF(8, size - 15 + i, bit(bt, i));
      setF(8, size - 8, true);
    }
    format(0);
    if (ver >= 7) {
      var r = ver;
      for (i = 0; i < 12; i++) r = (r << 1) ^ ((r >>> 11) * 0x1f25);
      var vb = (ver << 12) | r;
      for (i = 0; i < 18; i++) {
        var a = size - 11 + (i % 3), c = Math.floor(i / 3);
        setF(a, c, bit(vb, i)); setF(c, a, bit(vb, i));
      }
    }
    // Colocar los datos en zigzag
    var n = 0;
    for (var right = size - 1; right >= 1; right -= 2) {
      if (right === 6) right = 5;
      for (var vert = 0; vert < size; vert++) for (j = 0; j < 2; j++) {
        var x = right - j, up = ((right + 1) & 2) === 0, y = up ? size - 1 - vert : vert;
        if (!F[y][x] && n < cw.length * 8) { M[y][x] = bit(cw[n >>> 3], 7 - (n & 7)); n++; }
      }
    }
    function mask(m) {
      for (var y = 0; y < size; y++) for (var x = 0; x < size; x++) {
        var inv;
        switch (m) {
          case 0: inv = (x + y) % 2 === 0; break;
          case 1: inv = y % 2 === 0; break;
          case 2: inv = x % 3 === 0; break;
          case 3: inv = (x + y) % 3 === 0; break;
          case 4: inv = (Math.floor(x / 3) + Math.floor(y / 2)) % 2 === 0; break;
          case 5: inv = (x * y) % 2 + (x * y) % 3 === 0; break;
          case 6: inv = ((x * y) % 2 + (x * y) % 3) % 2 === 0; break;
          default: inv = ((x + y) % 2 + (x * y) % 3) % 2 === 0;
        }
        if (!F[y][x] && inv) M[y][x] = !M[y][x];
      }
    }
    // Penalización simplificada (rachas, bloques 2x2, balance) para elegir máscara
    function penalty() {
      var s = 0, dark = 0;
      for (var y = 0; y < size; y++) {
        var runR = 1, runC = 1;
        for (var x = 0; x < size; x++) {
          if (M[y][x]) dark++;
          if (x > 0) {
            if (M[y][x] === M[y][x - 1]) { runR++; if (runR === 5) s += 3; else if (runR > 5) s++; } else runR = 1;
            if (M[x][y] === M[x - 1][y]) { runC++; if (runC === 5) s += 3; else if (runC > 5) s++; } else runC = 1;
          }
          if (x > 0 && y > 0 && M[y][x] === M[y][x - 1] && M[y][x] === M[y - 1][x] && M[y][x] === M[y - 1][x - 1]) s += 3;
        }
      }
      var t = size * size;
      return s + Math.floor(Math.abs(dark * 20 - t * 10) / t) * 10;
    }
    var best = 0, bestP = Infinity;
    for (var m = 0; m < 8; m++) {
      mask(m); format(m);
      var pn = penalty();
      if (pn < bestP) { bestP = pn; best = m; }
      mask(m);
    }
    mask(best); format(best);
    return M;
  }

  function svg(text, o) {
    o = o || {};
    var M = matrix(text), m = o.margin == null ? 4 : o.margin, s = M.length + m * 2, d = "";
    for (var y = 0; y < M.length; y++) for (var x = 0; x < M.length; x++)
      if (M[y][x]) d += "M" + (x + m) + "," + (y + m) + "h1v1h-1z";
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ' + s + " " + s +
      '" shape-rendering="crispEdges"><rect width="' + s + '" height="' + s + '" fill="' +
      (o.light || "#fff") + '"/><path d="' + d + '" fill="' + (o.dark || "#000") + '"/></svg>';
  }

  var QR = { matrix: matrix, svg: svg };
  if (typeof module !== "undefined" && module.exports) module.exports = QR;
  else root.QR = QR;
})(this);
