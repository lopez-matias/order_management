(() => {
  const { api, escapeHTML, formatDate, formatMoney, statusBadge } = App;

  function metric(index, icon, label, data, money = false) {
    const variation = data.variation == null ? '<span>Sin comparación previa</span>' : `<span class="variation ${data.variation < 0 ? 'down' : ''}">${data.variation > 0 ? '↑' : data.variation < 0 ? '↓' : '→'} ${Math.abs(data.variation)}%</span><span>vs. mes anterior</span>`;
    return `<article class="metric-card"><span class="metric-index">0${index}</span><div class="metric-icon ${icon}"><svg><use href="#icon-${icon}"></use></svg></div><div class="metric-copy"><span>${label}</span><strong>${money ? formatMoney(data.value) : Number(data.value).toLocaleString('es-UY')}</strong><small>${variation}</small></div></article>`;
  }

  function drawChart(canvas, values) {
    const ratio = window.devicePixelRatio || 1;
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    canvas.width = width * ratio; canvas.height = height * ratio;
    const ctx = canvas.getContext('2d'); ctx.scale(ratio, ratio);
    const pad = { top: 15, right: 15, bottom: 30, left: 48 };
    const chartW = width - pad.left - pad.right, chartH = height - pad.top - pad.bottom;
    const maxRaw = Math.max(...values.map(item => Number(item.total)), 1);
    const max = Math.ceil(maxRaw / 1000) * 1000 || 1000;
    ctx.font = '9px IBM Plex Mono'; ctx.textAlign = 'right'; ctx.fillStyle = '#84877f';
    for (let i = 0; i <= 4; i++) {
      const y = pad.top + chartH * i / 4;
      ctx.beginPath(); ctx.strokeStyle = '#e6e4dc'; ctx.lineWidth = 1; ctx.moveTo(pad.left, y); ctx.lineTo(width - pad.right, y); ctx.stroke();
      const value = max * (4 - i) / 4;
      ctx.fillText(value >= 1000 ? `$${Math.round(value / 1000)}k` : `$${value}`, pad.left - 9, y + 3);
    }
    const points = values.map((item, index) => ({
      x: pad.left + chartW * index / Math.max(values.length - 1, 1),
      y: pad.top + chartH - (Number(item.total) / max) * chartH,
      ...item
    }));
    ctx.beginPath(); points.forEach((point, index) => index ? ctx.lineTo(point.x, point.y) : ctx.moveTo(point.x, point.y));
    ctx.lineTo(points.at(-1).x, pad.top + chartH); ctx.lineTo(points[0].x, pad.top + chartH); ctx.closePath();
    const fill = ctx.createLinearGradient(0, pad.top, 0, pad.top + chartH); fill.addColorStop(0, 'rgba(207,235,93,.26)'); fill.addColorStop(1, 'rgba(207,235,93,0)'); ctx.fillStyle = fill; ctx.fill();
    ctx.beginPath(); points.forEach((point, index) => index ? ctx.lineTo(point.x, point.y) : ctx.moveTo(point.x, point.y)); ctx.strokeStyle = '#151a17'; ctx.lineWidth = 2.2; ctx.stroke();
    points.forEach(point => { ctx.beginPath(); ctx.arc(point.x, point.y, 3.5, 0, Math.PI * 2); ctx.fillStyle = '#d9f45f'; ctx.fill(); ctx.strokeStyle = '#151a17'; ctx.lineWidth = 1.5; ctx.stroke(); });
    ctx.textAlign = 'center'; ctx.fillStyle = '#84877f'; ctx.font = '9px IBM Plex Mono'; points.forEach((point, index) => { if (index % 2 === 0 || values.length <= 7) ctx.fillText(point.label, point.x, height - 7); });
    canvas._points = points;
    canvas.onmousemove = event => {
      const rect = canvas.getBoundingClientRect(); const x = event.clientX - rect.left;
      const point = points.reduce((best, item) => Math.abs(item.x - x) < Math.abs(best.x - x) ? item : best, points[0]);
      const tooltip = document.querySelector('#chart-tooltip');
      if (Math.abs(point.x - x) < 28) { tooltip.textContent = `${point.label}: ${formatMoney(point.total)}`; tooltip.style.left = `${point.x}px`; tooltip.style.top = `${point.y}px`; tooltip.classList.remove('hidden'); } else tooltip.classList.add('hidden');
    };
    canvas.onmouseleave = () => document.querySelector('#chart-tooltip').classList.add('hidden');
  }

  async function load() {
    document.querySelector('#today-label').textContent = new Intl.DateTimeFormat('es-UY', { weekday: 'long', day: 'numeric', month: 'long' }).format(new Date());
    try {
      const data = await api('/api/dashboard');
      document.querySelector('#metrics').innerHTML = [
        metric(1, 'money', 'Ventas del mes', data.sales_this_month, true), metric(2, 'cart', 'Pedidos del mes', data.orders_this_month), metric(3, 'user', 'Clientes activos', data.active_customers), metric(4, 'clock', 'Cobros pendientes', data.pending_total, true)
      ].join('');
      document.querySelector('#top-customers').innerHTML = data.top_customers.length ? data.top_customers.map((item, i) => `<a href="/clientes" class="ranking-row"><span class="rank-number">${i + 1}</span><span class="rank-name"><strong>${escapeHTML(item.name)}</strong><span>${item.orders_count} ${item.orders_count === 1 ? 'pedido' : 'pedidos'}</span></span><strong>${formatMoney(item.total)}</strong></a>`).join('') : '<div class="empty-state"><strong>Aún no hay ventas</strong>Los clientes aparecerán aquí.</div>';
      document.querySelector('#top-products').innerHTML = data.top_products.length ? data.top_products.map(item => `<div class="product-row"><span class="product-box"><svg><use href="#icon-box"></use></svg></span><span><strong>${escapeHTML(item.name)}</strong><span>${escapeHTML(item.sku)}</span></span><span class="product-quantity"><strong>${item.quantity}</strong><span> unidades</span></span></div>`).join('') : '<div class="empty-state">Sin productos vendidos.</div>';
      document.querySelector('#recent-orders').innerHTML = data.recent_orders.length ? data.recent_orders.map(item => `<tr><td><a class="order-number" href="/pedidos/${item.id}">${escapeHTML(item.order_number)}</a></td><td><span class="cell-main">${escapeHTML(item.customer_name)}</span></td><td>${formatDate(item.order_date)}</td><td>${statusBadge(item.status)}</td><td>${statusBadge(item.payment_status)}</td><td class="align-right"><strong>${formatMoney(item.total)}</strong></td><td><a class="row-link" href="/pedidos/${item.id}" aria-label="Ver pedido"><svg><use href="#icon-arrow"></use></svg></a></td></tr>`).join('') : '<tr><td colspan="7"><div class="empty-inline">Aún no hay pedidos.</div></td></tr>';
      document.querySelector('#pending-count').textContent = data.pending_payments.length;
      document.querySelector('#pending-payments').innerHTML = data.pending_payments.length ? data.pending_payments.map(item => `<a href="/pedidos/${item.order_id}" class="pending-row"><span><strong>${escapeHTML(item.customer_name)}</strong><span>${escapeHTML(item.order_number)} · ${item.due_date ? `Vence ${formatDate(item.due_date)}` : 'Sin vencimiento'}</span></span><span class="pending-amount"><strong>${formatMoney(item.pending)}</strong><span>pendiente</span></span></a>`).join('') : '<div class="empty-state"><strong>Todo al día</strong>No hay cobros pendientes.</div>';
      const canvas = document.querySelector('#sales-chart');
      drawChart(canvas, data.monthly_sales);
      window.addEventListener('resize', App.debounce(() => drawChart(canvas, data.monthly_sales), 120));
    } catch (error) {
      App.toast(error.message, 'error');
    }
  }
  load();
})();
