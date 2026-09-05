(() => {
  const { api, escapeHTML, formatMoney, setButtonLoading, toast } = App;
  const form = document.querySelector('#order-form');
  const itemsContainer = document.querySelector('#order-items');
  const template = document.querySelector('#item-template');
  let products = [];

  function productOptions() {
    return '<option value="">Seleccionar producto…</option>' + products.map(product => `<option value="${product.id}" data-price="${product.price}">${escapeHTML(product.name)} · ${escapeHTML(product.sku)} · ${formatMoney(product.price)}</option>`).join('');
  }

  function addItem() {
    const fragment = template.content.cloneNode(true);
    const row = fragment.querySelector('.order-item');
    row.querySelector('.item-product').innerHTML = productOptions();
    row.querySelector('.item-product').addEventListener('change', calculate);
    row.querySelector('.item-quantity').addEventListener('input', calculate);
    row.querySelector('.remove-item').addEventListener('click', () => {
      if (itemsContainer.children.length === 1) return toast('El pedido debe tener al menos un producto.', 'error');
      row.remove(); calculate();
    });
    itemsContainer.append(row);
    calculate();
  }

  function calculate() {
    let subtotal = 0;
    itemsContainer.querySelectorAll('.order-item').forEach(row => {
      const select = row.querySelector('.item-product');
      const price = Number(select.selectedOptions[0]?.dataset.price || 0);
      const quantity = Math.max(0, Number(row.querySelector('.item-quantity').value || 0));
      row.querySelector('.item-price').textContent = formatMoney(price);
      row.querySelector('.item-total').textContent = formatMoney(price * quantity);
      subtotal += price * quantity;
    });
    const discount = Math.max(0, Number(document.querySelector('#order-discount').value || 0));
    document.querySelector('#order-subtotal').textContent = formatMoney(subtotal);
    document.querySelector('#order-total').textContent = formatMoney(Math.max(0, subtotal - discount));
  }

  async function initialize() {
    const today = new Date();
    form.elements.order_date.value = today.toISOString().slice(0, 10);
    const due = new Date(today); due.setDate(due.getDate() + 15);
    form.elements.due_date.value = due.toISOString().slice(0, 10);
    try {
      const [customerData, productData, users] = await Promise.all([
        api('/api/customers?active=true&page_size=100'),
        api('/api/products?active=true&page_size=100'),
        api('/api/users')
      ]);
      products = productData.items;
      document.querySelector('#order-customer').innerHTML = '<option value="">Seleccionar cliente…</option>' + customerData.items.map(customer => `<option value="${customer.id}">${escapeHTML(customer.name)} · ${escapeHTML(customer.document)}</option>`).join('');
      document.querySelector('#order-user').innerHTML = '<option value="">Sin asignar</option>' + users.map(user => `<option value="${user.id}">${escapeHTML(user.full_name)}</option>`).join('');
      addItem();
      if (!customerData.items.length || !products.length) {
        const error = document.querySelector('#order-error');
        error.textContent = 'Necesitas al menos un cliente y un producto activos para crear un pedido.';
        error.classList.remove('hidden');
      }
    } catch (error) { toast(error.message, 'error'); }
  }

  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (!form.reportValidity()) return;
    const items = [...itemsContainer.querySelectorAll('.order-item')].map(row => ({
      product_id: Number(row.querySelector('.item-product').value),
      quantity: Number(row.querySelector('.item-quantity').value)
    }));
    const unique = new Set(items.map(item => item.product_id));
    const errorNode = document.querySelector('#order-error');
    if (unique.size !== items.length) { errorNode.textContent = 'Un producto aparece más de una vez. Ajusta la cantidad en una sola fila.'; errorNode.classList.remove('hidden'); return; }
    const body = {
      customer_id: Number(form.elements.customer_id.value),
      created_by_id: form.elements.created_by_id.value ? Number(form.elements.created_by_id.value) : null,
      order_date: form.elements.order_date.value,
      due_date: form.elements.due_date.value || null,
      discount: Number(form.elements.discount.value || 0),
      notes: form.elements.notes.value.trim() || null,
      items
    };
    const button = form.querySelector('[type=submit]'); setButtonLoading(button, true, 'Creando pedido…'); errorNode.classList.add('hidden');
    try { const order = await api('/api/orders', { method: 'POST', body }); window.location.assign(`/pedidos/${order.id}?created=1`); }
    catch (error) { errorNode.textContent = error.message; errorNode.classList.remove('hidden'); errorNode.scrollIntoView({ behavior: 'smooth', block: 'center' }); setButtonLoading(button, false); }
  });
  document.querySelector('#add-item').addEventListener('click', addItem);
  document.querySelector('#order-discount').addEventListener('input', calculate);
  initialize();
})();

