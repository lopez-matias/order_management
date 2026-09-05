(() => {
  const { api, escapeHTML, formatDate, formatMoney, initials, setButtonLoading, statusBadge, toast, confirmAction } = App;
  const id = document.body.dataset.orderId;
  let order;

  function paidTotal() { return order.payments.filter(payment => payment.status === 'completed').reduce((sum, payment) => sum + Number(payment.amount), 0); }
  function render() {
    document.querySelector('#order-detail-loading').classList.add('hidden'); document.querySelector('#order-detail').classList.remove('hidden');
    document.querySelector('#detail-number').textContent = order.order_number;
    document.querySelector('#detail-status').innerHTML = statusBadge(order.status);
    document.querySelector('#detail-created').textContent = `Registrado el ${formatDate(order.created_at)}`;
    document.querySelector('#detail-item-count').textContent = `${order.items.length} ${order.items.length === 1 ? 'artículo' : 'artículos'} en este pedido`;
    document.querySelector('#detail-items').innerHTML = order.items.map(item => `<tr><td><span class="cell-main">${escapeHTML(item.product_name)}</span></td><td>${escapeHTML(item.product_sku)}</td><td class="align-right">${item.quantity}</td><td class="align-right">${formatMoney(item.unit_price)}</td><td class="align-right"><strong>${formatMoney(item.line_total)}</strong></td></tr>`).join('');
    document.querySelector('#detail-subtotal').textContent = formatMoney(order.subtotal); document.querySelector('#detail-discount').textContent = `− ${formatMoney(order.discount)}`; document.querySelector('#detail-total').textContent = formatMoney(order.total);
    document.querySelector('#detail-initials').textContent = initials(order.customer.name); document.querySelector('#detail-customer').textContent = order.customer.name; document.querySelector('#detail-document').textContent = order.customer.document; document.querySelector('#detail-history-link').href = `/clientes?customer=${order.customer_id}`;
    document.querySelector('#detail-date').textContent = formatDate(order.order_date); document.querySelector('#detail-due').textContent = formatDate(order.due_date); document.querySelector('#detail-user').textContent = order.created_by?.full_name || 'Sin asignar'; document.querySelector('#detail-payment-status').innerHTML = statusBadge(order.payment_status);
    const notesCard = document.querySelector('#notes-card'); if (order.notes) document.querySelector('#detail-notes').textContent = order.notes; else notesCard.classList.add('hidden');
    const paymentArea = document.querySelector('#detail-payments');
    paymentArea.innerHTML = order.payments.length ? `<div class="table-scroll payments-table"><table><thead><tr><th>FECHA</th><th>MEDIO</th><th>REFERENCIA</th><th>ESTADO</th><th class="align-right">IMPORTE</th></tr></thead><tbody>${order.payments.map(payment => `<tr><td>${formatDate(payment.paid_at)}</td><td>${escapeHTML(payment.method)}</td><td>${escapeHTML(payment.reference || '—')}</td><td>${statusBadge(payment.status)}</td><td class="align-right"><strong>${formatMoney(payment.amount)}</strong></td></tr>`).join('')}</tbody></table></div>` : '<div class="payment-empty">Aún no se registraron pagos.</div>';
    const outstanding = Math.max(0, Number(order.total) - paidTotal());
    document.querySelector('#add-payment').classList.toggle('hidden', outstanding <= 0 || order.status === 'cancelled');
    document.querySelector('#payment-pending').textContent = formatMoney(outstanding); document.querySelector('#payment-form').elements.amount.max = outstanding.toFixed(2); document.querySelector('#payment-form').elements.amount.value = outstanding.toFixed(2);
    const actions = document.querySelector('#status-actions'); actions.innerHTML = '';
    if (order.status === 'confirmed') actions.innerHTML = '<button class="btn btn-ghost" data-status="cancelled">Cancelar pedido</button><button class="btn btn-primary" data-status="completed"><svg><use href="#icon-check"></use></svg>Marcar completado</button>';
    if (order.status === 'draft') actions.innerHTML = '<button class="btn btn-ghost" data-status="cancelled">Cancelar pedido</button><button class="btn btn-primary" data-status="confirmed">Confirmar pedido</button>';
    actions.querySelectorAll('[data-status]').forEach(button => button.addEventListener('click', () => changeStatus(button.dataset.status)));
  }
  async function load() { try { order = await api(`/api/orders/${id}`); render(); if (new URLSearchParams(location.search).has('created')) toast('Pedido creado correctamente.'); } catch (error) { document.querySelector('#order-detail-loading').textContent = error.message; } }
  async function changeStatus(status) { const label = App.statusLabels[status].toLowerCase(); if (!await confirmAction(`El pedido pasará a estado ${label}. Esta acción no podrá revertirse.`, 'Continuar')) return; try { order = await api(`/api/orders/${id}`, { method: 'PATCH', body: { status } }); toast('Estado actualizado.'); render(); } catch (error) { toast(error.message, 'error'); } }
  const paymentModal = document.querySelector('#payment-modal');
  document.querySelector('#add-payment').addEventListener('click', () => paymentModal.classList.remove('hidden'));
  document.querySelectorAll('[data-close-payment]').forEach(button => button.addEventListener('click', () => paymentModal.classList.add('hidden')));
  document.querySelector('#payment-form').addEventListener('submit', async event => { event.preventDefault(); const form = event.currentTarget; if (!form.reportValidity()) return; const button = form.querySelector('[type=submit]'); const body = { amount: Number(form.elements.amount.value), method: form.elements.method.value, reference: form.elements.reference.value.trim() || null, notes: form.elements.notes.value.trim() || null }; setButtonLoading(button, true); try { await api(`/api/orders/${id}/payments`, { method: 'POST', body }); paymentModal.classList.add('hidden'); form.reset(); toast('Pago registrado.'); await load(); } catch (error) { const node = document.querySelector('#payment-error'); node.textContent = error.message; node.classList.remove('hidden'); } finally { setButtonLoading(button, false); } });
  load();
})();
