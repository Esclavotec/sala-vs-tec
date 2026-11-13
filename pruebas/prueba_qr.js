const QR=require('/home/claude/sala-vs-tec/qr.js');const fs=require('fs');
const texts=['https://sala-vs-tec.web.app/?c=AMOR26','hola','https://una-direccion-bastante-larga-para-probar-version-alta.web.app/completa.html?c=AMOR26&x=123456789'];
texts.forEach((t,i)=>{const M=QR.matrix(t);const sc=8,m=4,n=M.length+2*m;let rows=[];for(let y=0;y<n;y++){let r=[];for(let x=0;x<n;x++){const d=(y>=m&&x>=m&&y<n-m&&x<n-m)&&M[y-m][x-m];r.push(d?0:255)}rows.push(r)}fs.writeFileSync('qr'+i+'.json',JSON.stringify({rows,sc}));console.log(t.length,M.length)});
