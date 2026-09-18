const http=require('node:http');
const fs=require('node:fs');
const path=require('node:path');
const root=path.resolve(__dirname,'../outputs/khaneh-portraits');
const mime={'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'text/javascript; charset=utf-8','.json':'application/json','.svg':'image/svg+xml','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.woff2':'font/woff2','.glb':'model/gltf-binary','.blend':'application/x-blender','.txt':'text/plain'};
const server=http.createServer((req,res)=>{
  if(!['GET','HEAD'].includes(req.method)){res.writeHead(405).end();return;}
  let pathname;try{pathname=decodeURIComponent(new URL(req.url,'http://127.0.0.1').pathname);}catch{res.writeHead(400).end();return;}
  const target=path.resolve(root,'.'+(pathname==='/'?'/atlas.html':pathname));
  if(!target.startsWith(root+path.sep)||!mime[path.extname(target)]){res.writeHead(403).end();return;}
  fs.readFile(target,(error,data)=>{if(error){res.writeHead(404).end('Not found');return;}res.writeHead(200,{'Content-Type':mime[path.extname(target)],'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Content-Length':data.length});res.end(req.method==='HEAD'?undefined:data);});
});
server.listen(4173,'127.0.0.1',()=>console.log('Khaneh preview: http://127.0.0.1:4173'));

