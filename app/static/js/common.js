(() => {
  const moneyFormatter = new Intl.NumberFormat('es-UY', {
    style: 'currency', currency: 'UYU', minimumFractionDigits: 2
  });
  const dateFormatter = new Intl.DateTimeFormat('es-UY', {
    day: '2-digit', month: 'short', year: 'numeric'
  });
  const statusLabels = {
    draft: 'Borrador', confirmed: 'Confirmado', completed: 'Completado', cancelled: 'Cancelado',
    pending: 'Pendiente', partial: 'Parcial', paid: 'Pagado', overdue: 'Vencido',
    refunded: 'Reintegrado', active: 'Activo', inactive: 'Inactivo'
  };

  function escapeHTML(value) {
    return String(value ?? '').replace(/[&<>'"]/g, char => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
    })[char]);
  }

  function formatMoney(value) {
    return moneyFormatter.format(Number(value || 0)).replace('UYU', '$');
  }

  function formatDate(value) {
    if (!value) return '—';
    const raw = String(value).slice(0, 10);
    const [year, month, day] = raw.split('-').map(Number);
    return dateFormatter.format(new Date(year, month - 1, day));
  }

  function statusBadge(value) {
    return `<span class="status status-${escapeHTML(value)}">${statusLabels[value] || escapeHTML(value)}</span>`;
  }

  async function api(path, options = {}) {
    const config = { ...options, headers: { ...options.headers } };
    if (config.body && !(config.body instanceof FormData)) {
      config.headers['Content-Type'] = 'application/json';
      if (typeof config.body !== 'string') config.body = JSON.stringify(config.body);
    }
    const response = await fetch(path, config);
    if (response.status === 204) return null;
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const validation = data.errors?.map(item => `${item.field}: ${item.message}`).join('. ');
      throw new Error(validation || data.detail || 'No se pudo completar la operación.');
    }
    return data;
  }

  function toast(message, type = 'success') {
    const element = document.createElement('div');
    element.className = `toast ${type}`;
    element.textContent = message;
    document.querySelector('#toast-container').append(element);
    window.setTimeout(() => element.remove(), 3500);
  }

  function debounce(callback, wait = 300) {
    let timeout;
    return (...args) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => callback(...args), wait);
    };
  }

  function initials(name) {
    return String(name || '').split(/\s+/).filter(Boolean).slice(0, 2).map(word => word[0]).join('').toUpperCase();
  }

  function pagination(container, data, onPage) {
    const pages = Math.max(1, Math.ceil(data.total / data.page_size));
    const start = data.total ? (data.page - 1) * data.page_size + 1 : 0;
    const end = Math.min(data.page * data.page_size, data.total);
    const candidates = new Set([1, pages, data.page - 1, data.page, data.page + 1]);
    const pageButtons = [...candidates].filter(page => page >= 1 && page <= pages).sort((a, b) => a - b);
    let previous = 0;
    const buttons = pageButtons.map(page => {
      const gap = previous && page - previous > 1 ? '<span>…</span>' : '';
      previous = page;
      return `${gap}<button class="page-button ${page === data.page ? 'active' : ''}" data-page="${page}">${page}</button>`;
    }).join('');
    container.innerHTML = `<span>Mostrando ${start}–${end} de ${data.total}</span><div class="pagination-controls"><button class="page-button" data-page="${data.page - 1}" ${data.page <= 1 ? 'disabled' : ''}>‹</button>${buttons}<button class="page-button" data-page="${data.page + 1}" ${data.page >= pages ? 'disabled' : ''}>›</button></div>`;
    container.querySelectorAll('[data-page]:not([disabled])').forEach(button => {
      button.addEventListener('click', () => onPage(Number(button.dataset.page)));
    });
  }

  function confirmAction(message, confirmLabel = 'Confirmar') {
    const modal = document.querySelector('#confirm-modal');
    const messageNode = document.querySelector('#confirm-message');
    const action = document.querySelector('#confirm-action');
    messageNode.textContent = message;
    action.textContent = confirmLabel;
    modal.classList.remove('hidden');
    return new Promise(resolve => {
      const close = result => {
        modal.classList.add('hidden');
        action.removeEventListener('click', accept);
        modal.querySelectorAll('[data-close-modal]').forEach(button => button.removeEventListener('click', cancel));
        resolve(result);
      };
      const accept = () => close(true);
      const cancel = () => close(false);
      action.addEventListener('click', accept);
      modal.querySelectorAll('[data-close-modal]').forEach(button => button.addEventListener('click', cancel));
    });
  }

  function setButtonLoading(button, loading, text = 'Guardando…') {
    if (loading) {
      button.dataset.label = button.innerHTML;
      button.textContent = text;
      button.disabled = true;
    } else {
      button.innerHTML = button.dataset.label || button.innerHTML;
      button.disabled = false;
    }
  }

  document.querySelector('#menu-toggle')?.addEventListener('click', () => {
    document.querySelector('#sidebar').classList.toggle('open');
  });
  document.addEventListener('click', event => {
    if (window.innerWidth <= 800 && !event.target.closest('#sidebar') && !event.target.closest('#menu-toggle')) {
      document.querySelector('#sidebar')?.classList.remove('open');
    }
  });

  window.App = { api, debounce, escapeHTML, formatDate, formatMoney, initials, pagination, setButtonLoading, statusBadge, statusLabels, toast, confirmAction };
})();

