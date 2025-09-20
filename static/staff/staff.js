(function(){
  const qs = (s)=>document.querySelector(s);
  const csrf = ()=>document.cookie.split('; ').find(x=>x.startsWith('nq_csrf='))?.split('=')[1];
  const loginSection=qs('#login'), queueSection=qs('#queue'), ordersEl=qs('#orders'), ding=qs('#ding');

  qs('#loginForm').onsubmit=async(e)=>{
    const f=new FormData(e.target);
    const r=await fetch('/api/staff/login', {method:'POST', headers:{'Content-Type':'application/json','X-CSRF-Token': csrf()}, body: JSON.stringify({username:f.get('username'), password:f.get('password')})});
    const data=await r.json();
    if(r.ok){ loginSection.hidden=true; queueSection.hidden=false; connectWS(); loadOrders(); } else { qs('#loginMsg').textContent=data.detail||'Login failed'; }
  };

  qs('#refreshBtn').onclick=()=>loadOrders();
  qs('#filterState').onchange=()=>loadOrders();

  async function loadOrders(){
    const state=qs('#filterState').value;
    const r=await fetch('/api/staff/orders'+(state?`?state=${encodeURIComponent(state)}`:''));
    if(!r.ok){ ordersEl.textContent='Not authorized'; return; }
    const data=await r.json(); renderOrders(data.orders);
  }

  function renderOrders(list){
    ordersEl.innerHTML='';
    list.forEach(o=>{
      const card=document.createElement('div'); card.className='card';
      const row=document.createElement('div'); row.className='row';
      row.innerHTML=`<div><strong>Table ${o.table_id}</strong> — <span class="badge">${o.state}</span></div><div>${new Date(o.created_at).toLocaleTimeString()}</div>`;
      const actions=document.createElement('div');
      ['accept','ready','served','void'].forEach(a=>{
        const b=document.createElement('button'); b.textContent=a; b.onclick=()=>act(o.id,a); actions.appendChild(b);
      });
      card.appendChild(row); card.appendChild(actions);
      ordersEl.appendChild(card);
    });
  }

  async function act(id, action){
    const path=action==='void'?`/api/staff/orders/${id}/void`:`/api/staff/orders/${id}/${action}`;
    const headers={'X-CSRF-Token': csrf(),'Content-Type':'application/json'};
    const body=action==='void'?JSON.stringify({reason:prompt('Reason?')||''}):null;
    const r=await fetch(path,{method:'POST', headers, body});
    if(r.ok) loadOrders();
  }

  function connectWS(){
    const url=`${location.protocol==='https:'?'wss':'ws'}://${location.host}/ws/staff`;
    const ws=new WebSocket(url);
    ws.onmessage=(ev)=>{
      try{
        const msg=JSON.parse(ev.data);
        if(msg.event==='order_submitted'){ ding.play(); loadOrders(); flash(); }
        if(msg.event==='order_state_changed'){ loadOrders(); }
      }catch{}
    };
    ws.onclose=()=>setTimeout(connectWS, 2000);
  }

  function flash(){ document.body.style.background='#131'; setTimeout(()=>document.body.style.background='#111', 300); }
})();