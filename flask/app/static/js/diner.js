(function () {
  const socket = io();
  if (TABLE_CODE) {
    socket.emit('join_table', { table_code: TABLE_CODE });
    // Initial fetch
    refreshCart();
  }

  socket.on('cart_sync', (payload) => renderCart(payload));
  socket.on('order_submitted', (payload) => {
    $('#order-updates').prepend(
      `<div>Order #${payload.order_id} submitted (${payload.items.length} items)</div>`
    );
  });
  socket.on('order_status_update', (p) => {
    $('#order-updates').prepend(
      `<div>Order #${p.order_id} status: <strong>${p.status}</strong></div>`
    );
  });

  $(document).on('click', '.add-item', async function () {
    if (!TABLE_CODE) return;
    const id = $(this).data('id');
    await fetchJSON(`/api/table/${TABLE_CODE}/cart/add`, {
      method: 'POST',
      body: JSON.stringify({ menu_item_id: id, qty: 1 })
    });
  });

  $(document).on('click', '.remove-item', async function () {
    const cid = $(this).data('id');
    await fetchJSON(`/api/table/${TABLE_CODE}/cart/remove`, {
      method: 'POST',
      body: JSON.stringify({ cart_item_id: cid })
    });
  });

  $('#submit-order').on('click', async function () {
    if (!TABLE_CODE) return;
    const res = await fetchJSON(`/api/table/${TABLE_CODE}/submit`, { method: 'POST' });
    if (res.ok) {
      alert('Order submitted!');
    } else {
      alert(res.error || 'Unable to submit');
    }
  });

  async function refreshCart() {
    if (!TABLE_CODE) return;
    const data = await fetchJSON(`/api/table/${TABLE_CODE}/cart`);
    renderCart(data);
  }

  function renderCart(payload) {
    if (!payload || !payload.all_items) return;
    const $list = $('#cart-list').empty();
    if (!payload.all_items.length) {
      $list.html('<div class="text-muted">Cart is empty</div>');
      $('#cart-total').text('$0.00');
      return;
    }
    const groups = payload.per_user;
    Object.values(groups).forEach(g => {
      $list.append(`<div class="fw-bold mt-2">${g.user_label}</div>`);
      g.items.forEach(it => {
        $list.append(`
          <div class="d-flex justify-content-between align-items-center border-bottom py-1">
            <div>${it.qty} × ${_.escape(it.name)} <span class="text-muted small">${it.notes ? '('+_.escape(it.notes)+')' : ''}</span></div>
            <div>
              $${(it.price_cents*it.qty/100).toFixed(2)}
              <button class="btn btn-sm btn-outline-danger ms-2 remove-item" data-id="${it.cart_item_id}">&times;</button>
            </div>
          </div>
        `);
      });
    });
    $('#cart-total').text(payload.total_str);
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
