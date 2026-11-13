// Uso: node qr_png.js "<url>" salida.json  -> matriz para dibujar con Python
const QR=require('/home/claude/sala-vs-tec/qr.js');require('fs').writeFileSync(process.argv[3],JSON.stringify(QR.matrix(process.argv[2])));
