(() => {
  const { api, debounce, escapeHTML, formatDate, formatMoney, pagination, statusBadge } = App;
  const state = { page: 1, pageSize: 15 };
  const table = document.querySelector('#orders-table');
  async function load() {
    const params = new URLSearchParams({ page: state.page, page_size: state.pageSize });
    const values = { search: '#order-search', status: '#order-status', payment_status: '#payment-status', date_from: '#date-from', date_to: '#date-to' };
    Object.entries(values).forEach(([key, selector]) => { const value = document.querySelector(selector).value.trim(); if (value) params.set(key, value); });
    table.innerHTML = '<tr><td colspan="7"><div class="empty-inline">Cargando pedidos…</div></td></tr>';
    try { const data = await api(`/api/orders?${params}`); table.innerHTML = data.items.length ? data.items.map(order => `<tr><td><a class="order-number" href="/pedidos/${order.id}">${escapeHTML(order.order_number)}</a></td><td><span class="cell-main">${escapeHTML(order.customer.name)}</span><span class="cell-sub">${escapeHTML(order.customer.document)}</span></td><td>${formatDate(order.order_date)}</td><td>${statusBadge(order.status)}</td><td>${statusBadge(order.payment_status)}</td><td class="align-right"><strong>${formatMoney(order.total)}</strong></td><td><a class="row-link" href="/pedidos/${order.id}" aria-label="Ver pedido"><svg><use href="#icon-arrow"></use></svg></a></td></tr>`).join('') : '<tr><td colspan="7"><div class="empty-state"><strong>No encontramos pedidos</strong>Ajusta los filtros o crea una nueva operación.</div></td></tr>'; pagination(document.querySelector('#orders-pagination'), data, page => { state.page = page; load(); }); } catch (error) { table.innerHTML = `<tr><td colspan="7"><div class="empty-state">${escapeHTML(error.message)}</div></td></tr>`; }
  }
  document.querySelector('#order-search').addEventListener('input', debounce(() => { state.page = 1; load(); })); ['#order-status', '#payment-status', '#date-from', '#date-to'].forEach(selector => document.querySelector(selector).addEventListener('change', () => { state.page = 1; load(); })); load();
})();
