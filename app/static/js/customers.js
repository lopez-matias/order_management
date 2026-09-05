(() => {
  const { api, debounce, escapeHTML, formatDate, formatMoney, initials, pagination, setButtonLoading, statusBadge, toast, confirmAction } = App;
  const state = { page: 1, pageSize: 15, search: '', active: 'true' };
  const table = document.querySelector('#customers-table');
  const modal = document.querySelector('#customer-modal');
  const form = document.querySelector('#customer-form');

  async function load() {
    table.innerHTML = '<tr><td colspan="6"><div class="empty-inline">Cargando clientes…</div></td></tr>';
    const params = new URLSearchParams({ page: state.page, page_size: state.pageSize });
    if (state.search) params.set('search', state.search);
    if (state.active !== '') params.set('active', state.active);
    try {
      const data = await api(`/api/customers?${params}`);
      table.innerHTML = data.items.length ? data.items.map(customer => `<tr><td><span class="cell-main">${escapeHTML(customer.name)}</span><span class="cell-sub">${escapeHTML(customer.address || 'Sin dirección')}</span></td><td>${escapeHTML(customer.document)}</td><td><span class="cell-main">${escapeHTML(customer.email || '—')}</span><span class="cell-sub">${escapeHTML(customer.phone || 'Sin teléfono')}</span></td><td>${statusBadge(customer.active ? 'active' : 'inactive')}</td><td>${formatDate(customer.created_at)}</td><td><div class="table-actions"><button class="icon-button" data-history="${customer.id}" title="Historial"><svg><use href="#icon-clock"></use></svg></button><button class="icon-button" data-edit="${customer.id}" title="Editar"><svg><use href="#icon-edit"></use></svg></button>${customer.active ? `<button class="icon-button danger" data-delete="${customer.id}" data-name="${escapeHTML(customer.name)}" title="Desactivar"><svg><use href="#icon-trash"></use></svg></button>` : ''}</div></td></tr>`).join('') : '<tr><td colspan="6"><div class="empty-state"><strong>No encontramos clientes</strong>Prueba con otra búsqueda o registra uno nuevo.</div></td></tr>';
      pagination(document.querySelector('#customers-pagination'), data, page => { state.page = page; load(); });
    } catch (error) { table.innerHTML = `<tr><td colspan="6"><div class="empty-state">${escapeHTML(error.message)}</div></td></tr>`; }
  }

  function close() { modal.classList.add('hidden'); form.reset(); document.querySelector('#customer-error').classList.add('hidden'); }
  function open(customer = null) {
    form.reset(); form.elements.id.value = customer?.id || '';
    for (const field of ['name', 'document', 'email', 'phone', 'address', 'notes']) form.elements[field].value = customer?.[field] || '';
    document.querySelector('#customer-modal-title').textContent = customer ? 'Editar cliente' : 'Nuevo cliente';
    modal.classList.remove('hidden'); setTimeout(() => form.elements.name.focus(), 50);
  }

  table.addEventListener('click', async event => {
    const edit = event.target.closest('[data-edit]'), remove = event.target.closest('[data-delete]'), history = event.target.closest('[data-history]');
    if (edit) { try { open(await api(`/api/customers/${edit.dataset.edit}`)); } catch (error) { toast(error.message, 'error'); } }
    if (remove && await confirmAction(`El cliente "${remove.dataset.name}" quedará inactivo, pero su historial se conservará.`, 'Desactivar')) { try { await api(`/api/customers/${remove.dataset.delete}`, { method: 'DELETE' }); toast('Cliente desactivado.'); load(); } catch (error) { toast(error.message, 'error'); } }
    if (history) showHistory(history.dataset.history);
  });

  async function showHistory(id) {
    const historyModal = document.querySelector('#history-modal'), content = document.querySelector('#customer-history');
    historyModal.classList.remove('hidden'); content.innerHTML = '<div class="empty-inline">Cargando historial…</div>';
    try {
      const [customer, orders] = await Promise.all([api(`/api/customers/${id}`), api(`/api/customers/${id}/orders?page_size=100`)]);
      document.querySelector('#history-title').textContent = customer.name;
      content.innerHTML = orders.items.length ? `<div class="table-scroll"><table><thead><tr><th>PEDIDO</th><th>FECHA</th><th>ESTADO</th><th>PAGO</th><th class="align-right">TOTAL</th></tr></thead><tbody>${orders.items.map(order => `<tr><td><a class="order-number" href="/pedidos/${order.id}">${escapeHTML(order.order_number)}</a></td><td>${formatDate(order.order_date)}</td><td>${statusBadge(order.status)}</td><td>${statusBadge(order.payment_status)}</td><td class="align-right"><strong>${formatMoney(order.total)}</strong></td></tr>`).join('')}</tbody></table></div>` : '<div class="empty-state"><strong>Sin compras registradas</strong>Este cliente aún no tiene pedidos.</div>';
    } catch (error) { content.innerHTML = `<div class="empty-state">${escapeHTML(error.message)}</div>`; }
  }

  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (!form.reportValidity()) return;
    const button = form.querySelector('[type=submit]'), id = form.elements.id.value;
    const body = Object.fromEntries(new FormData(form)); delete body.id;
    Object.keys(body).forEach(key => { if (body[key] === '') body[key] = null; });
    setButtonLoading(button, true);
    try { await api(id ? `/api/customers/${id}` : '/api/customers', { method: id ? 'PUT' : 'POST', body }); close(); toast(id ? 'Cliente actualizado.' : 'Cliente creado.'); load(); }
    catch (error) { const node = document.querySelector('#customer-error'); node.textContent = error.message; node.classList.remove('hidden'); }
    finally { setButtonLoading(button, false); }
  });
  document.querySelector('#new-customer').addEventListener('click', () => open());
  document.querySelectorAll('[data-close-customer]').forEach(button => button.addEventListener('click', close));
  document.querySelectorAll('[data-close-history]').forEach(button => button.addEventListener('click', () => document.querySelector('#history-modal').classList.add('hidden')));
  document.querySelector('#customer-search').addEventListener('input', debounce(event => { state.search = event.target.value.trim(); state.page = 1; load(); }));
  document.querySelector('#customer-status').addEventListener('change', event => { state.active = event.target.value; state.page = 1; load(); });
  load();
})();

