(function () {
  const socket = io();
  socket.emit('join_kitchen', {});
  socket.on('order_submitted', (o) => {
    loadOrders(); // simple: refresh list on events
  });
  socket.on('order_status_update', (o) => {
    loadOrders();
  });

  async function loadOrders() {
    const orders = await fetchJSON('/staff/api/orders');
    renderOrders(orders);
    renderStats(orders);
  }
  loadOrders();

  function renderOrders(orders) {
    const $board = $('#orders-board').empty();
    const statusClasses = {
      submitted: 'secondary',
      acknowledged: 'warning',
      preparing: 'primary',
      ready: 'success',
      served: 'dark',
      cancelled: 'danger'
    };
    orders.forEach(o => {
      const itemsHtml = o.items.map(i => 
        `<div>${i.qty} × ${_.escape(i.name)} <span class="small text-muted">${i.notes? '('+_.escape(i.notes)+')':''}</span></div>`
      ).join('');
      const status = o.status;
      const card = $(`
        <div class="col-12 col-md-6">
          <div class="card order-card shadow-sm">
            <div class="card-body">
              <div class="d-flex justify-content-between align-items-center">
                <div><strong>Table ${o.table_label}</strong> <span class="text-muted">(${o.table_code})</span></div>
                <span class="badge bg-${statusClasses[status]||'secondary'}">${status}</span>
              </div>
              <div class="small-muted mt-1">#${o.order_id} • ${timeAgo(o.created_at)}</div>
              <div class="mt-2">${itemsHtml}</div>
              <div class="mt-2 d-flex gap-2 flex-wrap">
                ${['acknowledged','preparing','ready','served','cancelled'].map(s => `
                   <button class="btn btn-sm btn-outline-${statusClasses[s]||'secondary'} btn-status" data-id="${o.order_id}" data-status="${s}">${s}</button>
                `).join('')}
              </div>
            </div>
          </div>
        </div>
      `);
      $board.append(card);
    });
  }

  $(document).on('click', '.btn-status', async function () {
    const id = $(this).data('id');
    const s = $(this).data('status');
    await fetchJSON(`/staff/api/order/${id}/status`, {
      method: 'POST',
      body: JSON.stringify({status: s})
    });
  });

  function renderStats(orders) {
    const counts = _.countBy(orders, 'status');
    const ctx = document.getElementById('statsChart');
    if (!ctx) return;
    if (window._stats) window._stats.destroy();
    window._stats = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: Object.keys(counts),
        datasets: [{ label: 'Orders', data: Object.values(counts) }]
      },
      options: { responsive: true, maintainAspectRatio: false }
    });
  }

  function timeAgo(iso) {
    const t = new Date(iso).getTime();
    const d = Date.now() - t;
    const mins = Math.floor(d/60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins} min ago`;
    const hrs = Math.floor(mins/60);
    return `${hrs} hr ${mins%60} min ago`;
  }

  async function fetchJSON(url, opts={}) {
    const res = await fetch(url, {
      headers: {'Content-Type': 'application/json'},
      credentials: 'same-origin',
      ...opts
    });
    return res.json();
  }
})();
