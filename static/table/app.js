(function(){
  const qs = (s)=>document.querySelector(s);
  const tableOpaque = location.pathname.split('/t/')[1] || '';
  if('serviceWorker' in navigator){
    navigator.serviceWorker.register('/static/table/service-worker.js').catch(()=>{});
  }
  const anonKey='nq_anon_id';
  const deviceKey='nq_device_id';
  const sessionCapKey='nq_session_cap';
  const tableTokenKey='nq_table_token';
  const changeQueueKey='nq_queue';
  const genId=()=>crypto.randomUUID();
  const deviceId=localStorage.getItem(deviceKey) || (localStorage.setItem(deviceKey, genId()), localStorage.getItem(deviceKey));
  const anonId=localStorage.getItem(anonKey) || (localStorage.setItem(anonKey, ('anon-'+Math.random().toString(36).slice(2,10))), localStorage.getItem(anonKey));
  const tableToken = localStorage.getItem(tableTokenKey) || (localStorage.setItem(tableTokenKey, makeOpaqueToken(tableOpaque)), localStorage.getItem(tableTokenKey));

  function makeOpaqueToken(opaque){ 
    // Client stores bootstrap info; server accepts signed token, JSON, or raw opaque.
    return btoa(JSON.stringify({tab: opaque, bootstrap:true}));
  }

  const state={menu:{categories:[],items:[]}, cart:{cart_id:null, items:[]}, table_name:'', session_id:null, session_cap:null, ws:null};

  async function startSession(){
    const r=await fetch('/api/public/session/start', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({table_token: atob(tableToken), device_id: deviceId})
    });
    if(!r.ok){ alert('Bad table token'); return; }
    const data=await r.json();
    state.session_id=data.session_id; state.session_cap=data.session_cap; state.table_id=data.table_id; qs('#tableName').textContent=data.table_name;
    localStorage.setItem(sessionCapKey, data.session_cap);
  }

  async function loadMenu(){
    const r = await fetch('/api/public/menu?table_token='+encodeURIComponent(atob(tableToken)));
    const data = await r.json();
    state.menu=data;
    renderMenu();
  }

  async function loadCart(){
    const r=await fetch('/api/public/cart?table_token='+encodeURIComponent(atob(tableToken))+'&session_cap='+encodeURIComponent(state.session_cap));
    if(!r.ok) return;
    const data = await r.json();
    state.cart = data;
    renderCart();
  }

  function optimisticAdd(item){
    const client_uid=genId();
    const entry={id:'pending:'+client_uid, client_uid, item_id:item.id, title:item.title_i18n?.en||'Item', quantity:1, options:{}, notes:null, added_by:anonId, state:'in_cart'};
    state.cart.items.push(entry);
    renderCart();
    const idem=genId();
    enqueueChange({type:'add', payload:{client_uid, item_id:item.id, quantity:1, options:{}, notes:null}, idem});
    flushQueue();
  }

  function enqueueChange(ev){
    const q = JSON.parse(localStorage.getItem(changeQueueKey)||'[]');
    q.push(ev);
    localStorage.setItem(changeQueueKey, JSON.stringify(q));
  }

  async function flushQueue(){
    if(!navigator.onLine) return;
    const q = JSON.parse(localStorage.getItem(changeQueueKey)||'[]');
    if(q.length===0) return;
    const ev=q.shift();
    localStorage.setItem(changeQueueKey, JSON.stringify(q));
    try{
      if(ev.type==='add'){
        const r=await fetch('/api/public/cart/items?table_token='+encodeURIComponent(atob(tableToken))+'&session_cap='+encodeURIComponent(state.session_cap)+'&anon_user_id='+encodeURIComponent(anonId), {
          method:'POST', headers:{'Content-Type':'application/json', 'Idempotency-Key': ev.idem},
          body: JSON.stringify(ev.payload)
        });
        if(r.ok){ const data=await r.json(); state.cart=data; renderCart(); }
      }
    }catch(e){
      // requeue with backoff
      setTimeout(()=>{ enqueueChange(ev); }, 1000);
    }
    if(JSON.parse(localStorage.getItem(changeQueueKey)||'[]').length>0){ flushQueue(); }
  }

  function connectWS(){
    if(state.ws){ try{state.ws.close();}catch{} }
    const url=`${location.protocol==='https:'?'wss':'ws'}://${location.host}/ws/table?token=${encodeURIComponent(atob(tableToken))}&session_id=${encodeURIComponent(state.session_id)}&session_cap=${encodeURIComponent(state.session_cap)}`;
    const ws=new WebSocket(url);
    ws.onopen=()=>{};
    ws.onmessage=(ev)=>{
      try{
        const msg=JSON.parse(ev.data);
        if(msg.event==='cart_updated'){ loadCart(); }
        if(msg.event==='order_submitted'){ notify('Order submitted'); }
        if(msg.event==='order_state_changed'){ notify('Order '+msg.data.state); }
        if(msg.event==='menu_updated'){ loadMenu(); }
      }catch{}
    };
    ws.onclose=()=>{ setTimeout(connectWS, 2000); };
    state.ws=ws;
  }

  function renderMenu(){
    const cats=qs('#categories'); cats.innerHTML='';
    state.menu.categories.forEach((c,i)=>{
      const b=document.createElement('button'); b.className='tab'; b.textContent=c.title_i18n?.en || 'Category'; b.setAttribute('role','tab'); b.setAttribute('aria-selected', i===0 ? 'true':'false');
      b.onclick=()=>{ document.querySelectorAll('.tab').forEach(x=>x.setAttribute('aria-selected','false')); b.setAttribute('aria-selected','true'); renderItems(c.id); };
      cats.appendChild(b);
    });
    if(state.menu.categories[0]) renderItems(state.menu.categories[0].id);
  }
  function renderItems(catId){
    const el=qs('#items'); el.innerHTML='';
    const items=state.menu.items.filter(i=>i.category_id===catId && !i.is_86);
    items.forEach(it=>{
      const div=document.createElement('div'); div.className='card';
      const t=document.createElement('div'); t.textContent=(it.title_i18n?.en)||'Item';
      const p=document.createElement('div'); p.className='muted'; p.textContent=`$${it.price}`;
      const btn=document.createElement('button'); btn.className='primary'; btn.textContent='Add';
      btn.onclick=()=>optimisticAdd(it);
      div.append(t,p,btn); el.appendChild(div);
    });
  }
  function renderCart(){
    const ul=qs('#cartItems'); ul.innerHTML='';
    state.cart.items.forEach(ci=>{
      const li=document.createElement('li'); li.textContent=`${ci.quantity} × ${ci.title}`;
      ul.appendChild(li);
    });
  }

  function notify(msg){ try{ if(window.Notification && Notification.permission==='granted'){ new Notification(msg); } }catch{} }

  qs('#submitBtn').onclick=async()=>{
    const idem=genId();
    const r=await fetch('/api/public/cart/submit?table_token='+encodeURIComponent(atob(tableToken))+'&session_cap='+encodeURIComponent(state.session_cap)+'&anon_user_id='+encodeURIComponent(anonId), {method:'POST', headers:{'Idempotency-Key': idem}});
    if(r.ok){ const d=await r.json(); qs('#cartStatus').textContent='Submitted!'; }
  };
  qs('#hcToggle').onclick=()=>{ document.body.classList.toggle('hc'); };

  // Bootstrap
  (async function(){
    await startSession();
    await loadMenu();
    await loadCart();
    connectWS();
    setInterval(flushQueue, 1500);
  })();
})();