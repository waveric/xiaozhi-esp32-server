// ========== API 工具函数 ==========

async function api(method, url, body = null) {
    const opts = {
        method,
        headers: { 'Content-Type': 'application/json' }
    };
    if (body && method !== 'GET') {
        opts.body = JSON.stringify(body);
    }
    const res = await fetch(url, opts);
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || '请求失败');
    }
    return res.json();
}

// ========== Toast 提示 ==========

function showToast(msg, duration = 2500) {
    const el = document.getElementById('toast');
    el.textContent = msg;
    el.hidden = false;
    clearTimeout(el._timer);
    el._timer = setTimeout(() => { el.hidden = true; }, duration);
}

// ========== 分页渲染 ==========

function renderPagination(total, page, pageSize) {
    const container = document.getElementById('pagination');
    if (!container) return;

    const totalPages = Math.ceil(total / pageSize);
    if (totalPages <= 1) { container.innerHTML = ''; return; }

    let html = '';
    html += `<button ${page <= 1 ? 'disabled' : ''} onclick="loadPage(${page - 1})">上一页</button>`;

    // 显示页码（最多 7 个）
    let start = Math.max(1, page - 3);
    let end = Math.min(totalPages, start + 6);
    start = Math.max(1, end - 6);

    for (let i = start; i <= end; i++) {
        html += `<button class="${i === page ? 'active' : ''}" onclick="loadPage(${i})">${i}</button>`;
    }

    html += `<button ${page >= totalPages ? 'disabled' : ''} onclick="loadPage(${page + 1})">下一页</button>`;
    container.innerHTML = html;
}

// ========== HTML 转义 ==========

function esc(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// ========== 日期格式化 ==========

function formatDate(dateStr) {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    if (isNaN(d)) return dateStr;
    return `${d.getMonth() + 1}/${d.getDate()}`;
}
