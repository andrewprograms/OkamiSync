self.addEventListener('install', e=>{
  e.waitUntil((async()=>{
    const cache=await caches.open('nq-v1');
    await cache.addAll(['/static/table/styles.css','/static/table/app.js','/static/offline.html']);
  })());
});
self.addEventListener('fetch', e=>{
  e.respondWith((async()=>{
    try{
      return await fetch(e.request);
    }catch{
      const cache=await caches.open('nq-v1');
      const url = new URL(e.request.url);
      if(url.pathname.startsWith('/static/')){
        return (await cache.match(url.pathname)) || Response.error();
      }
      return await cache.match('/static/offline.html');
    }
  })());
});