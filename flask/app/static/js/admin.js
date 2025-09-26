(function () {
  // Add category
  $('#form-add-cat').on('submit', async function (e) {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(this));
    data.sort_order = Number(data.sort_order || 0);
    try {
      const res = await fetchJSON('/admin/api/menu/category', { method: 'POST', body: JSON.stringify(data) });
      if (res.ok) {
        showToast('Category added', 'success');
        this.reset();
        setTimeout(() => location.reload(), 350);
      } else {
        showToast(res.error || 'Error adding category', 'danger');
      }
    } catch (err) {
      showToast('Network error while adding category', 'danger');
    }
  });

  // Add item
  $('#form-add-item').on('submit', async function (e) {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(this));
    data.category_id = Number(data.category_id);
    data.price_cents = Number(data.price_cents);
    data.is_active = true;
    try {
      const res = await fetchJSON('/admin/api/menu/item', { method: 'POST', body: JSON.stringify(data) });
      if (res.ok) {
        showToast('Item added', 'success');
        this.reset();
        setTimeout(() => location.reload(), 350);
      } else {
        showToast(res.error || 'Unable to add item', 'danger');
      }
    } catch {
      showToast('Network error while adding item', 'danger');
    }
  });

  // Create table
  $('#btn-add-table').on('click', async function () {
    const code = $('#table-code').val().trim();
    const label = $('#table-label').val().trim();
    if (!code || !label) return showToast('Provide code and label', 'warning');
    try {
      const res = await fetchJSON('/admin/api/table', { method: 'POST', body: JSON.stringify({ code, label }) });
      if (res.ok) {
        showToast('Table created', 'success');
        setTimeout(() => location.reload(), 350);
      } else showToast(res.error || 'Error creating table', 'danger');
    } catch {
      showToast('Network error while creating table', 'danger');
    }
  });

  // Copy table link
  $(document).on('click', '.btn-copy-link', async function () {
    const link = $(this).data('link');
    try {
      await navigator.clipboard.writeText(link);
      showToast('Link copied to clipboard', 'success');
    } catch {
      showToast('Unable to copy link', 'danger');
    }
  });

  // Item search (client-side)
  $('#item-search').on('input', function () {
    const q = this.value.toLowerCase();
    $('#item-list .list-group-item').each(function () {
      const hay = (this.getAttribute('data-search') || '').toLowerCase();
      $(this).toggle(hay.includes(q));
    });
  });

  async function fetchJSON(url, opts = {}) {
    const res = await fetch(url, {
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      ...opts
    });
    // try reading JSON either on 2xx or error
    const json = await res.json().catch(() => ({}));
    return json;
  }
})();
