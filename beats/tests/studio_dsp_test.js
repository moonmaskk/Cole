// Optionaler Browser-Test fuers Handy-Autotune (braucht Node + Playwright):
//   node beats/tests/studio_dsp_test.js beats/web/studio.html
const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage();
const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.goto('file://'+require('path').resolve(process.argv[2]));
const r=await p.evaluate(async()=>{const D=window.ColeDSP,sr=44100,out={};
 function voice(fn,sec){const x=new Float32Array(sr*sec);let ph=0;for(let i=0;i<x.length;i++){const f=fn(i/sr);ph+=2*Math.PI*f/sr;
   x[i]=0.3*(Math.sin(ph)+0.5*Math.sin(2*ph)+0.33*Math.sin(3*ph)+0.25*Math.sin(4*ph));}return x}
 function measure(x,from,to){const fs=[];for(let s=Math.floor(from*sr);s<to*sr-4096;s+=2048){const xd=new Float32Array(1024);for(let i=0;i<1024;i++)xd[i]=0.5*(x[s+2*i]+x[s+2*i+1]);fs.push(D.detect(xd,0,1024,sr/2))}
   fs.sort((a,b)=>a-b);return +fs[fs.length>>1].toFixed(1)}
 const P={tau:0,amount:1,verb:0};
 let x=voice(()=>452,2); out.in452=measure(x,.3,1.7); out.am452=measure(D.autotune(x,sr,9,'min',P),.3,1.7);
 x=voice(()=>310,2); out.in310=measure(x,.3,1.7); out.am310=measure(D.autotune(x,sr,9,'min',P),.3,1.7); // D#4 ~ 311 -> nicht in Am -> D(293.7) oder E(329.6)
 x=voice(()=>180,2); out.c180=measure(D.autotune(x,sr,0,'maj',P),.3,1.7); // F#3 185 -> G 196 or F 174.6
 x=voice(t=>220*Math.pow(2,t/2/12*3),2); const y=D.autotune(x,sr,9,'min',P); out.len=[x.length,y.length];
 let mx=0;for(const v of y)mx=Math.max(mx,Math.abs(v));out.peak=+mx.toFixed(2);
 const t0=performance.now();D.autotune(voice(()=>300,30),sr,9,'min',P);out.ms30s=Math.round(performance.now()-t0);
 const ch=await D.chain(voice(()=>440,1),sr,{verb:.15});out.chain=[ch.numberOfChannels,ch.length];
 const w=D.wav([new Float32Array(100)],sr);out.wav=w.size;
 return out});
console.log(JSON.stringify(r),errs);await b.close()})();
