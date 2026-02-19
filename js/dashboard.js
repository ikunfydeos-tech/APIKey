// Dashboard 页面脚本 - 重构版（无管理员，用户自助）

// API 基础地址
const API_BASE_URL = 'http://localhost:8000';

// XSS 防护：HTML 转义函数
function escapeHtml(text) {
    if (text === null || text === undefined) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 数据存储
let apiKeys = [];
let providers = {};
let allModels = [];
let currentPage = 'keys';
let usageTimeRange = 7;

// 分页状态
let logsPage = 1;
let loginPage = 1;
const pageSize = 20;

// 服务商图标映射
const providerIconMap = {
    'openai': 'brain',
    'anthropic': 'bot',
    'google': 'sparkles',
    'azure': 'cloud',
    'deepseek': 'cpu',
    'moonshot': 'moon',
    'zhipu': 'zap',
    'baidu': 'globe',
    'alibaba': 'hexagon',
    'custom': 'link'
};

// DOM 元素引用
let keysTableBody, emptyState, addModal, deleteModal, keyForm;
let providerSelect, modelSelect;
let editingKeyId = null;
let deletingKeyId = null;

// 获取认证头
function getAuthHeaders() {
    const token = localStorage.getItem('token');
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };
}

// Toast 通知
function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <i data-lucide="${type === 'success' ? 'check-circle' : type === 'error' ? 'x-circle' : 'alert-circle'}"></i>
        <span>${escapeHtml(message)}</span>
    `;
    container.appendChild(toast);
    lucide.createIcons();
    
    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// 页面初始化
document.addEventListener('DOMContentLoaded', async function() {
    // 初始化DOM引用
    keysTableBody = document.getElementById('keysTableBody');
    emptyState = document.getElementById('emptyState');
    addModal = document.getElementById('addModal');
    deleteModal = document.getElementById('deleteModal');
    keyForm = document.getElementById('keyForm');
    providerSelect = document.getElementById('provider');
    modelSelect = document.getElementById('model');
    
    // URL参数处理
    const urlParams = new URLSearchParams(window.location.search);
    const page = urlParams.get('page');
    
    // 设置初始页面
    if (['usage', 'logs', 'security'].includes(page)) {
        switchToPage(page);
    } else {
        switchToPage('keys');
    }
    
    // 移除CSS闪烁控制
    document.documentElement.removeAttribute('data-initial-page');
    
    // 检查登录状态
    const isLoggedIn = await checkLoginStatus();
    if (isLoggedIn) {
        displayUsername();
        await loadProviders();
        await loadKeys();
    }
    
    initEventListeners();
});

// 检查登录状态
async function checkLoginStatus() {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = 'index.html';
        return false;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/me`, {
            headers: getAuthHeaders()
        });
        
        if (!response.ok) {
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            window.location.href = 'index.html';
            return false;
        }
        
        const user = await response.json();
        localStorage.setItem('user', JSON.stringify(user));
        return true;
    } catch (error) {
        console.error('验证登录状态失败:', error);
        return false;
    }
}

// 显示用户名
function displayUsername() {
    const userStr = localStorage.getItem('user');
    if (userStr) {
        const user = JSON.parse(userStr);
        const usernameDisplay = document.getElementById('usernameDisplay');
        if (usernameDisplay) {
            usernameDisplay.textContent = user.username || '用户';
        }
        const roleDisplay = document.getElementById('userRoleDisplay');
        if (roleDisplay) {
            roleDisplay.textContent = '用户';
        }
    }
}

// 初始化事件监听
function initEventListeners() {
    // 密钥表单提交
    if (keyForm) {
        keyForm.addEventListener('submit', handleKeyFormSubmit);
    }
    
    // 搜索框
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(searchKeys, 300));
    }
}

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

// ============ 页面切换 ============

function switchToPage(page) {
    currentPage = page;
    
    // 隐藏所有页面
    document.querySelectorAll('.content-area > div').forEach(el => {
        el.style.display = 'none';
    });
    
    // 显示目标页面
    const pageMap = {
        'keys': 'keyManagePage',
        'usage': 'usagePage',
        'logs': 'logsPage',
        'security': 'securityPage'
    };
    
    const targetPage = document.getElementById(pageMap[page]);
    if (targetPage) {
        targetPage.style.display = 'block';
    }
    
    // 更新导航高亮
    updateNavActive(`nav${page.charAt(0).toUpperCase() + page.slice(1)}`);
    
    // 更新面包屑
    const nameMap = {
        'keys': '密钥管理',
        'usage': '使用统计',
        'logs': '操作日志',
        'security': '安全中心'
    };
    const currentPageName = document.getElementById('currentPageName');
    if (currentPageName) {
        currentPageName.textContent = nameMap[page] || '密钥管理';
    }
    
    // 加载数据
    if (page === 'usage') loadUsageData();
    if (page === 'logs') loadLogs();
    if (page === 'security') loadSecurityData();
}

function switchToKeyManage() { switchToPage('keys'); loadKeys(); }
function switchToUsage() { switchToPage('usage'); }
function switchToLogs() { switchToPage('logs'); }
function switchToSecurity() { switchToPage('security'); }

function updateNavActive(navId) {
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    const navEl = document.getElementById(navId);
    if (navEl) navEl.classList.add('active');
}

// ============ 密钥管理 ============

async function loadProviders() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/keys/providers`, {
            headers: getAuthHeaders()
        });
        
        if (response.ok) {
            const data = await response.json();
            providers = {};
            data.forEach(p => {
                providers[p.id] = p;
            });
            
            // 填充服务商下拉框
            if (providerSelect) {
                providerSelect.innerHTML = '<option value="">请选择服务商</option>';
                data.forEach(p => {
                    providerSelect.innerHTML += `<option value="${p.id}">${escapeHtml(p.display_name || p.name)}</option>`;
                });
            }
            
            // 更新统计
            document.getElementById('totalProviders').textContent = data.length;
        }
    } catch (error) {
        console.error('加载服务商失败:', error);
    }
}

async function loadKeys() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/keys`, {
            headers: getAuthHeaders()
        });
        
        if (response.ok) {
            apiKeys = await response.json();
            renderKeysTable();
            updateKeyStats();
        }
    } catch (error) {
        console.error('加载密钥失败:', error);
        showToast('加载密钥失败', 'error');
    }
}

function renderKeysTable() {
    if (!keysTableBody) return;
    
    if (apiKeys.length === 0) {
        keysTableBody.innerHTML = '';
        if (emptyState) emptyState.style.display = 'flex';
        return;
    }
    
    if (emptyState) emptyState.style.display = 'none';
    
    keysTableBody.innerHTML = apiKeys.map(key => {
        const provider = providers[key.provider_id];
        const statusClass = key.status === 'active' ? 'active' : key.status === 'expired' ? 'expired' : 'inactive';
        const statusText = key.status === 'active' ? '活跃' : key.status === 'expired' ? '已过期' : '未激活';
        
        return `
            <tr>
                <td>
                    <div class="provider-cell">
                        <span class="provider-name">${escapeHtml(provider?.display_name || '未知')}</span>
                    </div>
                </td>
                <td>
                    <span class="key-name">${escapeHtml(key.key_name)}</span>
                </td>
                <td>${escapeHtml(key.model_id || '-')}</td>
                <td>
                    <code class="key-preview">${escapeHtml(key.api_key_preview || '-')}</code>
                </td>
                <td>
                    <span class="status-badge ${statusClass}">${statusText}</span>
                </td>
                <td>${key.expires_at ? formatDate(key.expires_at) : '-'}</td>
                <td>
                    <div class="action-buttons">
                        <button class="action-btn" onclick="editKey(${key.id})" title="编辑">
                            <i data-lucide="edit-2"></i>
                        </button>
                        <button class="action-btn renew" onclick="openRenewModal(${key.id}, '${escapeHtml(key.key_name)}')" title="续费">
                            <i data-lucide="credit-card"></i>
                        </button>
                        <button class="action-btn danger" onclick="openDeleteModal(${key.id})" title="删除">
                            <i data-lucide="trash-2"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
    
    lucide.createIcons();
}

function updateKeyStats() {
    const total = apiKeys.length;
    const active = apiKeys.filter(k => k.status === 'active').length;
    const expired = apiKeys.filter(k => k.status === 'expired').length;
    
    document.getElementById('totalKeys').textContent = total;
    document.getElementById('activeKeys').textContent = active;
    document.getElementById('expiredKeys').textContent = expired;
}

// 添加密钥弹窗
function openAddModal() {
    editingKeyId = null;
    document.getElementById('modalTitle').textContent = '添加API密钥';
    if (keyForm) keyForm.reset();
    if (addModal) addModal.classList.add('show');
}

function closeAddModal() {
    if (addModal) addModal.classList.remove('show');
    editingKeyId = null;
}

// 编辑密钥
async function editKey(keyId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/keys/${keyId}`, {
            headers: getAuthHeaders()
        });
        
        if (response.ok) {
            const key = await response.json();
            editingKeyId = keyId;
            
            document.getElementById('modalTitle').textContent = '编辑API密钥';
            document.getElementById('keyId').value = keyId;
            document.getElementById('provider').value = key.provider_id || '';
            document.getElementById('keyName').value = key.key_name || '';
            document.getElementById('apiKey').value = key.api_key || '';
            document.getElementById('keyNote').value = key.notes || '';
            
            if (addModal) addModal.classList.add('show');
        }
    } catch (error) {
        showToast('获取密钥详情失败', 'error');
    }
}

// 删除密钥
function openDeleteModal(keyId) {
    deletingKeyId = keyId;
    if (deleteModal) deleteModal.classList.add('show');
}

function closeDeleteModal() {
    if (deleteModal) deleteModal.classList.remove('show');
    deletingKeyId = null;
}

async function confirmDelete() {
    if (!deletingKeyId) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/keys/${deletingKeyId}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });
        
        if (response.ok) {
            showToast('密钥已删除');
            closeDeleteModal();
            loadKeys();
        } else {
            const data = await response.json();
            showToast(data.detail || '删除失败', 'error');
        }
    } catch (error) {
        showToast('删除失败', 'error');
    }
}

// 表单提交
async function handleKeyFormSubmit(e) {
    e.preventDefault();
    
    const keyData = {
        provider_id: parseInt(document.getElementById('provider').value),
        key_name: document.getElementById('keyName').value.trim(),
        api_key: document.getElementById('apiKey').value.trim(),
        notes: document.getElementById('keyNote').value.trim()
    };
    
    try {
        const url = editingKeyId 
            ? `${API_BASE_URL}/api/keys/${editingKeyId}`
            : `${API_BASE_URL}/api/keys`;
        
        const response = await fetch(url, {
            method: editingKeyId ? 'PUT' : 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(keyData)
        });
        
        if (response.ok) {
            showToast(editingKeyId ? '密钥已更新' : '密钥添加成功');
            closeAddModal();
            loadKeys();
        } else {
            const data = await response.json();
            showToast(data.detail || '操作失败', 'error');
        }
    } catch (error) {
        showToast('操作失败', 'error');
    }
}

// 搜索和筛选
function searchKeys() {
    const query = document.getElementById('searchInput')?.value.toLowerCase() || '';
    const statusFilter = document.getElementById('statusFilter')?.value || 'all';
    
    let filtered = apiKeys;
    
    if (query) {
        filtered = filtered.filter(k => 
            k.key_name.toLowerCase().includes(query) ||
            (k.model_id && k.model_id.toLowerCase().includes(query))
        );
    }
    
    if (statusFilter !== 'all') {
        filtered = filtered.filter(k => k.status === statusFilter);
    }
    
    renderFilteredKeys(filtered);
}

function filterByStatus() {
    searchKeys();
}

function renderFilteredKeys(keys) {
    if (!keysTableBody) return;
    
    if (keys.length === 0) {
        keysTableBody.innerHTML = '<tr><td colspan="7" class="empty-row">无匹配结果</td></tr>';
        return;
    }
    
    // 复用renderKeysTable的逻辑
    const originalKeys = apiKeys;
    apiKeys = keys;
    renderKeysTable();
    apiKeys = originalKeys;
}

// ============ 续费功能 ============

function openRenewModal(keyId, keyName) {
    document.getElementById('renewKeyId').value = keyId;
    document.getElementById('renewKeyName').textContent = keyName;
    document.getElementById('renewAmount').value = '';
    document.getElementById('renewDays').value = '30';
    document.getElementById('renewNote').value = '';
    
    const modal = document.getElementById('renewModal');
    if (modal) modal.classList.add('show');
}

function closeRenewModal() {
    const modal = document.getElementById('renewModal');
    if (modal) modal.classList.remove('show');
}

async function submitRenewal() {
    const keyId = document.getElementById('renewKeyId').value;
    const amount = parseFloat(document.getElementById('renewAmount').value);
    const durationDays = parseInt(document.getElementById('renewDays').value) || 30;
    const notes = document.getElementById('renewNote').value.trim();
    
    if (!amount || amount <= 0) {
        showToast('请输入有效的续费金额', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/user/renew`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                key_id: parseInt(keyId),
                amount: amount,
                duration_days: durationDays,
                notes: notes
            })
        });
        
        if (response.ok) {
            showToast('续费成功');
            closeRenewModal();
            loadKeys();
        } else {
            const data = await response.json();
            showToast(data.detail || '续费失败', 'error');
        }
    } catch (error) {
        showToast('续费失败', 'error');
    }
}

// ============ 使用统计 ============

async function loadUsageData() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/user/token-stats?days=${usageTimeRange}`, {
            headers: getAuthHeaders()
        });
        
        if (response.ok) {
            const data = await response.json();
            renderUsageStats(data);
        }
    } catch (error) {
        console.error('加载使用统计失败:', error);
    }
}

function setTimeRange(days) {
    usageTimeRange = days;
    
    // 更新按钮状态
    document.querySelectorAll('.time-btn').forEach(btn => {
        btn.classList.toggle('active', parseInt(btn.dataset.range) === days);
    });
    
    loadUsageData();
}

function renderUsageStats(data) {
    // 更新统计卡片
    document.getElementById('totalRequests').textContent = data.summary.total_requests.toLocaleString();
    document.getElementById('totalTokens').textContent = formatNumber(data.summary.total_tokens);
    document.getElementById('totalCost').textContent = `$${data.summary.total_cost.toFixed(2)}`;
    document.getElementById('activeKeysUsage').textContent = data.by_key?.length || 0;
    
    // 渲染图表
    renderTokenChart(data.daily_trend);
    renderProviderChart(data.by_provider);
    
    // 渲染模型使用表
    renderModelUsageTable(data.by_model);
}

function renderTokenChart(dailyData) {
    const ctx = document.getElementById('tokenChart');
    if (!ctx) return;
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: dailyData.map(d => d.date),
            datasets: [{
                label: 'Token消耗',
                data: dailyData.map(d => d.tokens),
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

function renderProviderChart(providerData) {
    const ctx = document.getElementById('providerChart');
    if (!ctx || !providerData?.length) return;
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: providerData.map(p => p.provider),
            datasets: [{
                data: providerData.map(p => p.tokens),
                backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'right' }
            }
        }
    });
}

function renderModelUsageTable(models) {
    const tbody = document.getElementById('modelUsageTableBody');
    if (!tbody || !models) return;
    
    tbody.innerHTML = models.map(m => `
        <tr>
            <td>${escapeHtml(m.model || '-')}</td>
            <td>-</td>
            <td>${m.requests?.toLocaleString() || 0}</td>
            <td>${formatNumber(m.tokens || 0)}</td>
            <td>-</td>
        </tr>
    `).join('');
}

// ============ 操作日志 ============

async function loadLogs() {
    const action = document.getElementById('logActionFilter')?.value || '';
    const status = document.getElementById('logStatusFilter')?.value || '';
    
    try {
        let url = `${API_BASE_URL}/api/user/logs?page=${logsPage}&page_size=${pageSize}`;
        if (action) url += `&action=${encodeURIComponent(action)}`;
        if (status) url += `&status=${status}`;
        
        const response = await fetch(url, {
            headers: getAuthHeaders()
        });
        
        if (response.ok) {
            const data = await response.json();
            renderLogsTable(data.items);
            updateLogsPagination(data.total, data.page);
            
            // 加载操作类型列表
            if (!document.getElementById('logActionFilter').options.length) {
                loadLogActions();
            }
        }
    } catch (error) {
        console.error('加载日志失败:', error);
    }
}

async function loadLogActions() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/user/log-actions`, {
            headers: getAuthHeaders()
        });
        
        if (response.ok) {
            const actions = await response.json();
            const select = document.getElementById('logActionFilter');
            if (select) {
                select.innerHTML = '<option value="">全部操作</option>';
                actions.forEach(a => {
                    select.innerHTML += `<option value="${escapeHtml(a)}">${escapeHtml(a)}</option>`;
                });
            }
        }
    } catch (error) {
        console.error('加载操作类型失败:', error);
    }
}

function renderLogsTable(logs) {
    const tbody = document.getElementById('logsTableBody');
    if (!tbody) return;
    
    if (!logs?.length) {
        tbody.innerHTML = '<tr><td colspan="6" class="empty-row">暂无日志记录</td></tr>';
        return;
    }
    
    tbody.innerHTML = logs.map(log => `
        <tr>
            <td>${formatDate(log.created_at)}</td>
            <td>${escapeHtml(log.action)}</td>
            <td>${escapeHtml(log.resource_name || '-')}</td>
            <td>${escapeHtml(log.ip_address || '-')}</td>
            <td>
                <span class="status-badge ${log.status === 'success' ? 'active' : 'inactive'}">
                    ${log.status === 'success' ? '成功' : '失败'}
                </span>
            </td>
            <td>${escapeHtml(log.details || '-')}</td>
        </tr>
    `).join('');
}

function updateLogsPagination(total, current) {
    const totalPages = Math.ceil(total / pageSize);
    document.getElementById('logsCurrentPage').textContent = current;
    document.getElementById('logsPrevBtn').disabled = current <= 1;
    document.getElementById('logsNextBtn').disabled = current >= totalPages;
}

function prevLogsPage() { if (logsPage > 1) { logsPage--; loadLogs(); } }
function nextLogsPage() { logsPage++; loadLogs(); }
function filterLogs() { logsPage = 1; loadLogs(); }

// ============ 安全中心 ============

async function loadSecurityData() {
    await Promise.all([
        loadLoginHistory(),
        loadBalances(),
        loadRenewals(),
        loadTOTPStatus()
    ]);
}

async function loadLoginHistory() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/user/login-history?page=${loginPage}&page_size=${pageSize}`, {
            headers: getAuthHeaders()
        });
        
        if (response.ok) {
            const data = await response.json();
            renderLoginHistory(data.items);
            updateLoginPagination(data.total, data.page);
        }
    } catch (error) {
        console.error('加载登录历史失败:', error);
    }
}

function renderLoginHistory(history) {
    const tbody = document.getElementById('loginHistoryBody');
    if (!tbody) return;
    
    if (!history?.length) {
        tbody.innerHTML = '<tr><td colspan="5" class="empty-row">暂无登录记录</td></tr>';
        return;
    }
    
    tbody.innerHTML = history.map(h => `
        <tr>
            <td>${formatDate(h.created_at)}</td>
            <td>${escapeHtml(h.ip_address)}</td>
            <td>${escapeHtml(truncate(h.user_agent, 30))}</td>
            <td>${h.login_type === 'totp' ? 'TOTP' : '密码'}</td>
            <td>
                <span class="status-badge ${h.status === 'success' ? 'active' : 'inactive'}">
                    ${h.status === 'success' ? '成功' : '失败'}
                </span>
            </td>
        </tr>
    `).join('');
}

function updateLoginPagination(total, current) {
    const totalPages = Math.ceil(total / pageSize);
    document.getElementById('loginCurrentPage').textContent = current;
    document.getElementById('loginPrevBtn').disabled = current <= 1;
    document.getElementById('loginNextBtn').disabled = current >= totalPages;
}

function prevLoginPage() { if (loginPage > 1) { loginPage--; loadLoginHistory(); } }
function nextLoginPage() { loginPage++; loadLoginHistory(); }

async function loadBalances() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/user/balances`, {
            headers: getAuthHeaders()
        });
        
        if (response.ok) {
            const balances = await response.json();
            renderBalances(balances);
        }
    } catch (error) {
        console.error('加载余额失败:', error);
    }
}

function renderBalances(balances) {
    const container = document.getElementById('balanceCards');
    if (!container) return;
    
    if (!balances?.length) {
        container.innerHTML = '<p class="empty-text">暂无余额信息</p>';
        return;
    }
    
    container.innerHTML = balances.map(b => `
        <div class="balance-card">
            <div class="balance-header">
                <span class="balance-key">${escapeHtml(b.key_name)}</span>
                <span class="balance-provider">${escapeHtml(b.provider || '-')}</span>
            </div>
            <div class="balance-amount">
                ${b.balance !== null ? `${b.currency} ${b.balance.toFixed(2)}` : '未查询'}
            </div>
            <div class="balance-stats">
                <span>使用: ${b.total_usage?.toFixed(2) || 0}</span>
                <span>请求: ${b.total_requests || 0}</span>
            </div>
            ${b.expires_at ? `<div class="balance-expires">过期: ${formatDate(b.expires_at)}</div>` : ''}
        </div>
    `).join('');
}

async function loadRenewals() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/user/renewals`, {
            headers: getAuthHeaders()
        });
        
        if (response.ok) {
            const data = await response.json();
            renderRenewals(data.items);
        }
    } catch (error) {
        console.error('加载续费记录失败:', error);
    }
}

function renderRenewals(renewals) {
    const tbody = document.getElementById('renewalsTableBody');
    if (!tbody) return;
    
    if (!renewals?.length) {
        tbody.innerHTML = '<tr><td colspan="5" class="empty-row">暂无续费记录</td></tr>';
        return;
    }
    
    tbody.innerHTML = renewals.map(r => `
        <tr>
            <td>${formatDate(r.created_at)}</td>
            <td>${escapeHtml(r.key_name || '-')}</td>
            <td>${r.currency} ${r.amount.toFixed(2)}</td>
            <td>${r.duration_days ? `${r.duration_days}天` : '-'}</td>
            <td>
                <span class="status-badge ${r.status === 'active' ? 'active' : 'inactive'}">
                    ${r.status === 'active' ? '有效' : '已过期'}
                </span>
            </td>
        </tr>
    `).join('');
}

async function loadTOTPStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/totp/status`, {
            headers: getAuthHeaders()
        });
        
        if (response.ok) {
            const data = await response.json();
            const statusEl = document.getElementById('totpStatus');
            if (statusEl) {
                statusEl.textContent = data.is_enabled ? '已启用' : '未启用';
                statusEl.className = `status-badge ${data.is_enabled ? 'enabled' : 'disabled'}`;
            }
        }
    } catch (error) {
        console.error('加载TOTP状态失败:', error);
    }
}

// TOTP功能
async function showBackupCodes() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/totp/backup-codes`, {
            headers: getAuthHeaders()
        });
        
        if (response.ok) {
            const data = await response.json();
            alert('备用验证码:\n\n' + data.backup_codes.join('\n') + '\n\n请妥善保管！');
        } else {
            showToast('获取备用码失败', 'error');
        }
    } catch (error) {
        showToast('获取备用码失败', 'error');
    }
}

async function showRegenerateTOTP() {
    if (!confirm('重新生成TOTP密钥后，您需要重新扫描二维码。确定继续吗？')) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/totp/regenerate`, {
            headers: getAuthHeaders()
        });
        
        if (response.ok) {
            const data = await response.json();
            showToast('请扫描新的二维码并验证');
            // 可以显示二维码弹窗
        } else {
            showToast('获取新密钥失败', 'error');
        }
    } catch (error) {
        showToast('获取新密钥失败', 'error');
    }
}

// 修改密码
function showChangePassword() {
    const modal = document.getElementById('changePasswordModal');
    if (modal) modal.classList.add('show');
}

function closeChangePasswordModal() {
    const modal = document.getElementById('changePasswordModal');
    if (modal) modal.classList.remove('show');
}

async function submitChangePassword() {
    const currentPassword = document.getElementById('currentPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmNewPassword').value;
    const totpCode = document.getElementById('totpForPassword').value;
    
    if (newPassword !== confirmPassword) {
        showToast('两次输入的密码不一致', 'error');
        return;
    }
    
    if (newPassword.length < 8) {
        showToast('密码长度至少8位', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/change-password`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword,
                totp_code: totpCode
            })
        });
        
        if (response.ok) {
            showToast('密码修改成功，请重新登录');
            closeChangePasswordModal();
            setTimeout(() => {
                localStorage.removeItem('token');
                localStorage.removeItem('user');
                window.location.href = 'index.html';
            }, 2000);
        } else {
            const data = await response.json();
            showToast(data.detail || '修改失败', 'error');
        }
    } catch (error) {
        showToast('修改失败', 'error');
    }
}

// 删除账户
function showDeleteAccount() {
    if (confirm('确定要删除账户吗？此操作不可恢复，所有数据将被永久删除！')) {
        const password = prompt('请输入密码确认：');
        const totpCode = prompt('请输入TOTP验证码：');
        
        if (password && totpCode) {
            deleteAccount(password, totpCode);
        }
    }
}

async function deleteAccount(password, totpCode) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/account`, {
            method: 'DELETE',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                password: password,
                totp_code: totpCode
            })
        });
        
        if (response.ok) {
            showToast('账户已删除');
            setTimeout(() => {
                localStorage.removeItem('token');
                localStorage.removeItem('user');
                window.location.href = 'index.html';
            }, 2000);
        } else {
            const data = await response.json();
            showToast(data.detail || '删除失败', 'error');
        }
    } catch (error) {
        showToast('删除失败', 'error');
    }
}

// ============ 工具函数 ============

function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatNumber(num) {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toLocaleString();
}

function truncate(str, len) {
    if (!str) return '';
    return str.length > len ? str.substring(0, len) + '...' : str;
}

// 密码显示切换
function toggleKeyPassword() {
    const input = document.getElementById('apiKey');
    if (input) {
        input.type = input.type === 'password' ? 'text' : 'password';
    }
}

// 侧边栏切换
function toggleSidebar() {
    document.querySelector('.app-layout').classList.toggle('sidebar-collapsed');
}

// 刷新数据
function refreshData() {
    if (currentPage === 'keys') loadKeys();
    else if (currentPage === 'usage') loadUsageData();
    else if (currentPage === 'logs') loadLogs();
    else if (currentPage === 'security') loadSecurityData();
    
    showToast('数据已刷新');
}

// 登出
async function handleLogout() {
    try {
        await fetch(`${API_BASE_URL}/api/logout`, {
            method: 'POST',
            headers: getAuthHeaders()
        });
    } catch (error) {
        console.error('登出请求失败:', error);
    }
    
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = 'index.html';
}

// 服务商选择变化
async function onProviderChange() {
    const providerId = document.getElementById('provider').value;
    if (!providerId || !modelSelect) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/keys/models/${providerId}`, {
            headers: getAuthHeaders()
        });
        
        if (response.ok) {
            const models = await response.json();
            modelSelect.innerHTML = '<option value="">请选择模型</option>';
            models.forEach(m => {
                modelSelect.innerHTML += `<option value="${m.model_id}">${escapeHtml(m.model_name || m.model_id)}</option>`;
            });
        }
    } catch (error) {
        console.error('加载模型失败:', error);
    }
}

// 测试API连接
async function testApiConnection() {
    const providerId = document.getElementById('provider').value;
    const apiKey = document.getElementById('apiKey').value;
    
    if (!providerId || !apiKey) {
        showToast('请选择服务商并输入密钥', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/keys/test`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                provider_id: parseInt(providerId),
                api_key: apiKey
            })
        });
        
        const data = await response.json();
        
        const resultRow = document.getElementById('testResultRow');
        const resultCard = document.getElementById('testResultCard');
        const resultIcon = document.getElementById('testResultIcon');
        const resultTitle = document.getElementById('testResultTitle');
        const resultMessage = document.getElementById('testResultMessage');
        
        if (resultRow && resultCard) {
            resultRow.style.display = 'block';
            resultCard.className = `test-result-card ${data.success ? 'success' : 'error'}`;
            resultIcon.innerHTML = data.success 
                ? '<i data-lucide="check-circle"></i>' 
                : '<i data-lucide="x-circle"></i>';
            resultTitle.textContent = data.success ? '连接成功' : '连接失败';
            resultMessage.textContent = data.message;
            lucide.createIcons();
        }
        
        showToast(data.message, data.success ? 'success' : 'error');
    } catch (error) {
        showToast('测试失败', 'error');
    }
}

// 服务商配置弹窗（保留原有功能）
function openProviderConfigModal() {
    const modal = document.getElementById('providerConfigModal');
    if (modal) modal.classList.add('show');
    loadProviderConfig();
}

function closeProviderConfigModal() {
    const modal = document.getElementById('providerConfigModal');
    if (modal) modal.classList.remove('show');
}

async function loadProviderConfig() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/keys/providers`, {
            headers: getAuthHeaders()
        });
        
        if (response.ok) {
            const providers = await response.json();
            const list = document.getElementById('providerConfigList');
            const count = document.getElementById('providerCount');
            
            if (count) count.textContent = providers.length;
            if (list) {
                list.innerHTML = providers.map(p => `
                    <div class="provider-item">
                        <div class="provider-info">
                            <span class="provider-name">${escapeHtml(p.display_name || p.name)}</span>
                            <span class="provider-url">${escapeHtml(p.base_url)}</span>
                        </div>
                        <span class="provider-status ${p.is_active ? 'active' : 'inactive'}">
                            ${p.is_active ? '已启用' : '已禁用'}
                        </span>
                    </div>
                `).join('');
            }
        }
    } catch (error) {
        console.error('加载服务商配置失败:', error);
    }
}

function openCustomProviderModal() {
    const modal = document.getElementById('customProviderModal');
    if (modal) modal.classList.add('show');
}

function closeCustomProviderModal() {
    const modal = document.getElementById('customProviderModal');
    if (modal) modal.classList.remove('show');
}

async function saveCustomProvider() {
    const name = document.getElementById('customProviderName').value.trim();
    const url = document.getElementById('customProviderUrl').value.trim();
    const desc = document.getElementById('customProviderDesc').value.trim();
    
    if (!name || !url) {
        showToast('请填写必填项', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/keys/providers`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                name: name.toLowerCase().replace(/\s+/g, '_'),
                display_name: name,
                base_url: url,
                description: desc,
                is_custom: true
            })
        });
        
        if (response.ok) {
            showToast('服务商添加成功');
            closeCustomProviderModal();
            loadProviders();
        } else {
            const data = await response.json();
            showToast(data.detail || '添加失败', 'error');
        }
    } catch (error) {
        showToast('添加失败', 'error');
    }
}