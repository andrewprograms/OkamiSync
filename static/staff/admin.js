(function(){
  const csrf = ()=>document.cookie.split('; ').find(x=>x.startsWith('nq_csrf='))?.split('=')[1];
  document.getElementById('catForm').onsubmit=async(e)=>{
    const f=new FormData(e.target);
    const data={title_i18n:{en:f.get('title_en')||'',ja:f.get('title_ja')||''}};
    const r=await fetch('/api/admin/categories',{method:'POST', headers:{'Content-Type':'application/json','X-CSRF-Token':csrf()}, body: JSON.stringify(data)});
    alert(r.ok?'Category created':'Failed');
  };
  document.getElementById('itemForm').onsubmit=async(e)=>{
    const f=new FormData(e.target);
    const data={title_i18n:{en:f.get('title_en')||''},price:parseFloat(f.get('price')||'0')};
    const r=await fetch('/api/admin/items',{method:'POST', headers:{'Content-Type':'application/json','X-CSRF-Token':csrf()}, body: JSON.stringify(data)});
    alert(r.ok?'Item created':'Failed');
  };
  document.getElementById('imgForm').onsubmit=async(e)=>{
    const f=new FormData(e.target);
    const r=await fetch('/api/admin/media',{method:'POST', headers:{'X-CSRF-Token':csrf()}, body: f});
    const data=await r.json();
    document.getElementById('imgResult').textContent=data.url||'Uploaded';
  };
})();