(function () {
  const socket = io();
  let currentFilter = 'active';
  const ACTIVE_SET = ['submitted', 'acknowledged', 'preparing', 'ready'];

  socket.emit('join_kitchen', {});
  socket.on('order_submitted', (o) => {
    showToast(`New order #${o.order_id} (${o.items.length} items)`, 'success');
    loadOrders();
  });
  socket.on('order_status_update', (o) => {
    showToast(`Order #${o.order_id} → ${o.status}`, 'primary');
    loadOrders();
  });

  $('#orderFilter').on('click', 'button[data-filter]', function () {
    $('#orderFilter button').removeClass('active');
    $(this).addClass('active');
    currentFilter = $(this).data('filter');
    loadOrders();
  });

  async function loadOrders() {
    const orders = await fetchJSON('/staff/api/orders').catch(() => []);
    renderOrders(applyFilter(orders));
    renderStats(orders);
  }
  loadOrders();

  function applyFilter(orders) {
    switch (currentFilter) {
      case 'served': return orders.filter(o => o.status === 'served');
      case 'cancelled': return orders.filter(o => o.status === 'cancelled');
      case 'active': return orders.filter(o => ACTIVE_SET.includes(o.status));
      default: return orders;
    }
  }

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
    if (!orders.length) {
      $board.append('<div class="col-12"><div class="alert alert-secondary">No orders in this view.</div></div>');
      return;
    }
    orders.forEach(o => {
      const itemsHtml = o.items.map(i =>
        `<div>${i.qty} × ${_.escape(i.name)} <span class="small text-muted">${i.notes ? '(' + _.escape(i.notes) + ')' : ''}</span></div>`
      ).join('');
      const status = o.status;
      const card = $(`
        <div class="col-12 col-md-6">
          <div class="card order-card shadow-sm">
            <div class="card-body">
              <div class="d-flex justify-content-between align-items-center">
                <div><strong>Table ${o.table_label}</strong> <span class="text-muted">(${o.table_code})</span></div>
                <span class="badge bg-${statusClasses[status] || 'secondary'}">${status}</span>
              </div>
              <div class="small-muted mt-1">#${o.order_id} • ${timeAgo(o.created_at)}</div>
              <div class="mt-2">${itemsHtml}</div>
              <div class="mt-2 d-flex gap-2 flex-wrap">
                ${['acknowledged', 'preparing', 'ready', 'served', 'cancelled'].map(s => `
                   <button class="btn btn-sm btn-outline-${statusClasses[s] || 'secondary'} btn-status" data-id="${o.order_id}" data-status="${s}">${s}</button>
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
    const res = await fetchJSON(`/staff/api/order/${id}/status`, {
      method: 'POST',
      body: JSON.stringify({ status: s })
    }).catch(() => ({}));
    if (res && res.ok) showToast(`Order #${id} set to ${s}`, 'success');
    else showToast(res?.error || 'Unable to update', 'danger');
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
    const mins = Math.floor(d / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins} min ago`;
    const hrs = Math.floor(mins / 60);
    return `${hrs} hr ${mins % 60} min ago`;
  }

  async function fetchJSON(url, opts = {}) {
    const res = await fetch(url, {
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      ...opts
    });
    return res.json();
  }
})();
