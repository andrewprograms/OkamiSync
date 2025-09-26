(function () {
  // Add category
  $('#form-add-cat').on('submit', async function (e) {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(this));
    data.sort_order = Number(data.sort_order||0);
    const res = await fetchJSON('/admin/api/menu/category', { method:'POST', body: JSON.stringify(data) });
    if (res.ok) location.reload();
  });

  // Add item
  $('#form-add-item').on('submit', async function (e) {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(this));
    data.category_id = Number(data.category_id);
    data.price_cents = Number(data.price_cents);
    data.is_active = true;
    const res = await fetchJSON('/admin/api/menu/item', { method:'POST', body: JSON.stringify(data) });
    if (res.ok) location.reload();
  });

  // Create table
  $('#btn-add-table').on('click', async function () {
    const code = $('#table-code').val().trim();
    const label = $('#table-label').val().trim();
    if (!code || !label) return alert('Provide code and label');
    const res = await fetchJSON('/admin/api/table', { method:'POST', body: JSON.stringify({code, label}) });
    if (res.ok) location.reload();
    else alert('Error creating table');
  });

  async function fetchJSON(url, opts={}) {
    const res = await fetch(url, {
      headers: {'Content-Type': 'application/json'},
      credentials: 'same-origin',
      ...opts
    });
    return res.json();
  }
})();
