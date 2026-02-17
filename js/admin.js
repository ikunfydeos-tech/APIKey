// 管理后台 JavaScript
const API_BASE_URL = 'http://localhost:8000';

// 动态管理员 API 前缀（启动时从后端获取）
let ADMIN_API_PREFIX = null;

// 状态管理
let currentPage = 'dashboard';
let currentUserPage = 1;
let usersPageSize = 20;
let logsPage = 1;
let logsPageSize = 50;
let logsData = [];
let registrationChart = null;
let providerChart = null;
let confirmCallback = null;
let highRiskConfirmAction = null;

// ============ 初始化 ============

document.addEventListener('DOMContentLoaded', async function() {
    // 验证访问路径
    if (!await verifyAdminAccess()) {
        return;
    }
    await checkAdminStatus();
    await initAdminApiPrefix();
    await loadDashboardData();
});

// 验证管理员访问路径
async function verifyAdminAccess() {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = 'index.html';
        return false;
    }
    
    // 检查 URL 参数中是否有有效的动态路径
    const urlParams = new URLSearchParams(window.location.search);
    const pathParam = urlParams.get('path');
    
    if (!pathParam) {
        // 没有路径参数，尝试从 API 获取
        try {
            const response = await fetch(`${API_BASE_URL}/api/admin-path`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            if (response.ok) {
                const data = await response.json();
                // 重定向到正确的 URL
                window.location.href = `admin.html?path=${data.admin_path}`;
                return false;
            } else {
                // 非 admin 用户
                showToast('无权限访问管理后台', 'error');
                window.location.href = 'dashboard.html';
                return false;
            }
        } catch (error) {
            console.error('验证管理员访问失败:', error);
            window.location.href = 'dashboard.html';
            return false;
        }
    }
    
    return true;
}

// 获取动态管理员 API 前缀
async function initAdminApiPrefix() {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = 'index.html';
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/api/admin-path`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            const data = await response.json();
            // 构建完整的 API 前缀: /api/sec/{admin_path}
            ADMIN_API_PREFIX = `${API_BASE_URL}/api/sec/${data.admin_path}`;
            console.log('[Security] Admin API initialized');
        } else {
            // 如果获取失败，可能是非管理员或服务异常
            showToast('无法获取管理接口', 'error');
            window.location.href = 'dashboard.html';
        }
    } catch (error) {
        console.error('初始化管理员 API 前缀失败:', error);
        showToast('初始化失败', 'error');
    }
}

// 检查管理员权限
async function checkAdminStatus() {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = 'index.html';
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/api/me`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) {
            localStorage.removeItem('token');
            window.location.href = 'index.html';
            return;
        }

        const user = await response.json();
        if (user.role !== 'admin') {
            showToast('无权限访问管理后台', 'error');
            window.location.href = 'dashboard.html';
            return;
        }

        document.getElementById('usernameDisplay').textContent = user.username;
    } catch (error) {
        console.error('检查管理员状态失败:', error);
        window.location.href = 'index.html';
    }
}

// 获取认证头
function getAuthHeaders() {
    const token = localStorage.getItem('token');
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };
}

// 获取管理员 API URL
function getAdminApiUrl(endpoint) {
    if (!ADMIN_API_PREFIX) {
        console.error('Admin API prefix not initialized');
        return null;
    }
    return `${ADMIN_API_PREFIX}${endpoint}`;
}

// ============ 页面切换 ============

function switchToDashboard() {
    currentPage = 'dashboard';
    hideAllPages();
    document.getElementById('dashboardPage').style.display = 'block';
    document.getElementById('currentPageName').textContent = '数据概览';
    setActiveNav('navDashboard');
    loadDashboardData();
}

function switchToUsers() {
    currentPage = 'users';
    hideAllPages();
    document.getElementById('usersPage').style.display = 'block';
    document.getElementById('currentPageName').textContent = '用户管理';
    setActiveNav('navUsers');
    loadUsers();
}

function switchToProviders() {
    currentPage = 'providers';
    hideAllPages();
    document.getElementById('providersPage').style.display = 'block';
    document.getElementById('currentPageName').textContent = '服务商管理';
    setActiveNav('navProviders');
    loadProviders();
}

function switchToModels() {
    currentPage = 'models';
    hideAllPages();
    document.getElementById('modelsPage').style.display = 'block';
    document.getElementById('currentPageName').textContent = '模型管理';
    setActiveNav('navModels');
    loadModels();
}

function switchToConfig() {
    currentPage = 'config';
    hideAllPages();
    document.getElementById('configPage').style.display = 'block';
    document.getElementById('currentPageName').textContent = '配置同步';
    setActiveNav('navConfig');
    loadConfigStatus();
}

function switchToLogs() {
    currentPage = 'logs';
    hideAllPages();
    document.getElementById('logsPage').style.display = 'block';
    document.getElementById('currentPageName').textContent = '日志审计';
    setActiveNav('navLogs');
    logsPage = 1;
    loadLogs();
    loadLogFilters();
}

function setActiveNav(navId) {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => item.classList.remove('active'));
    document.getElementById(navId).classList.add('active');
}

function hideAllPages() {
    document.getElementById('dashboardPage').style.display = 'none';
    document.getElementById('usersPage').style.display = 'none';
    document.getElementById('providersPage').style.display = 'none';
    document.getElementById('modelsPage').style.display = 'none';
    document.getElementById('configPage').style.display = 'none';
    document.getElementById('logsPage').style.display = 'none';
}

function setActiveNav(navId) {
    document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
    document.getElementById(navId).classList.add('active');
}

function refreshCurrentPage() {
    switch (currentPage) {
        case 'dashboard':
            loadDashboardData();
            break;
        case 'users':
            loadUsers();
            break;
        case 'providers':
            loadProviders();
            break;
        case 'models':
            loadModels();
            break;
        case 'config':
            loadConfigStatus();
            break;
        case 'logs':
            loadLogs();
            break;
        default:
            // 如果没有匹配的页面，刷新仪表板
            loadDashboardData();
            break;
    }
}

// ============ 数据概览 ============

async function loadDashboardData() {
    currentPage = 'dashboard';
    try {
        // 加载统计数据
        const [statsRes, providerStatsRes, trendRes] = await Promise.all([
            fetch(getAdminApiUrl('/stats/overview'), { headers: getAuthHeaders() }),
            fetch(getAdminApiUrl('/stats/providers'), { headers: getAuthHeaders() }),
            fetch(getAdminApiUrl('/stats/registration-trend?days=7'), { headers: getAuthHeaders() })
        ]);

        if (statsRes.ok) {
            const stats = await statsRes.json();
            document.getElementById('totalUsers').textContent = stats.users.total;
            document.getElementById('totalKeys').textContent = stats.keys.total;
            document.getElementById('activeProviders').textContent = stats.providers.active;
            document.getElementById('newUsersToday').textContent = stats.users.new_today;
        }

        if (providerStatsRes.ok) {
            const providerStats = await providerStatsRes.json();
            renderProviderChart(providerStats);
        }

        if (trendRes.ok) {
            const trend = await trendRes.json();
            renderRegistrationChart(trend);
        }
    } catch (error) {
        console.error('加载数据失败:', error);
        showToast('加载数据失败', 'error');
    }
}

function renderRegistrationChart(data) {
    const ctx = document.getElementById('registrationChart').getContext('2d');
    
    if (registrationChart) {
        registrationChart.destroy();
    }

    const labels = data.map(d => {
        const date = new Date(d.date);
        return `${date.getMonth() + 1}/${date.getDate()}`;
    });

    registrationChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: '新用户',
                    data: data.map(d => d.users),
                    borderColor: '#00d4aa',
                    backgroundColor: 'rgba(0, 212, 170, 0.1)',
                    tension: 0.4,
                    fill: true
                },
                {
                    label: '新密钥',
                    data: data.map(d => d.keys),
                    borderColor: '#6366f1',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    tension: 0.4,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#94a3b8' }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(148, 163, 184, 0.1)' },
                    ticks: { color: '#94a3b8' }
                },
                y: {
                    grid: { color: 'rgba(148, 163, 184, 0.1)' },
                    ticks: { color: '#94a3b8' }
                }
            }
        }
    });
}

function renderProviderChart(data) {
    const ctx = document.getElementById('providerChart').getContext('2d');
    
    if (providerChart) {
        providerChart.destroy();
    }

    const colors = ['#00d4aa', '#6366f1', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316', '#84cc16', '#06b6d4'];

    providerChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.map(d => d.provider),
            datasets: [{
                data: data.map(d => d.count),
                backgroundColor: colors.slice(0, data.length),
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: { color: '#94a3b8', padding: 10 }
                }
            }
        }
    });
}

// ============ 用户管理 ============

async function loadUsers() {
    currentPage = 'users';
    const search = document.getElementById('userSearchInput')?.value || '';
    const role = document.getElementById('roleFilter')?.value || '';
    const status = document.getElementById('statusFilter')?.value || '';

    try {
        const params = new URLSearchParams({
            page: currentUserPage,
            page_size: usersPageSize
        });
        if (search) params.append('search', search);
        if (role) params.append('role', role);
        if (status) params.append('status', status);

        const response = await fetch(getAdminApiUrl(`/users?${params}`), {
            headers: getAuthHeaders()
        });

        if (response.ok) {
            const data = await response.json();
            renderUsersTable(data.users);
            renderUsersPagination(data.total, data.page, data.page_size);
        }
    } catch (error) {
        console.error('加载用户失败:', error);
        showToast('加载用户失败', 'error');
    }
}

function renderUsersTable(users) {
    const tbody = document.getElementById('usersTableBody');
    tbody.innerHTML = '';

    users.forEach(user => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${user.id}</td>
            <td>${user.username}</td>
            <td>${user.email}</td>
            <td><span class="role-badge ${user.role}">${getRoleLabel(user.role)}</span></td>
            <td>${user.key_count}</td>
            <td><span class="status-badge ${user.is_active ? 'active' : 'inactive'}">${user.is_active ? '启用' : '禁用'}</span></td>
            <td>${formatDate(user.created_at)}</td>
            <td>
                <div class="action-buttons">
                    <button class="action-btn" onclick="viewUserDetail(${user.id})" title="查看详情">
                        <i data-lucide="eye"></i>
                    </button>
                    <button class="action-btn" onclick="toggleUserRole(${user.id}, '${user.role}')" title="切换角色">
                        <i data-lucide="shield"></i>
                    </button>
                    <button class="action-btn ${user.is_active ? 'danger' : 'success'}" onclick="toggleUserStatus(${user.id}, ${user.is_active})" title="${user.is_active ? '禁用' : '启用'}">
                        <i data-lucide="${user.is_active ? 'user-x' : 'user-check'}"></i>
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });

    lucide.createIcons();
}

function renderUsersPagination(total, page, pageSize) {
    const totalPages = Math.ceil(total / pageSize);
    const pagination = document.getElementById('usersPagination');
    pagination.innerHTML = '';

    if (totalPages <= 1) return;

    const prevBtn = document.createElement('button');
    prevBtn.className = `page-btn ${page === 1 ? 'disabled' : ''}`;
    prevBtn.textContent = '上一页';
    prevBtn.onclick = () => { if (page > 1) { currentUserPage = page - 1; loadUsers(); } };
    pagination.appendChild(prevBtn);

    for (let i = 1; i <= totalPages; i++) {
        if (i === 1 || i === totalPages || (i >= page - 2 && i <= page + 2)) {
            const btn = document.createElement('button');
            btn.className = `page-btn ${i === page ? 'active' : ''}`;
            btn.textContent = i;
            btn.onclick = () => { currentUserPage = i; loadUsers(); };
            pagination.appendChild(btn);
        } else if (i === page - 3 || i === page + 3) {
            const span = document.createElement('span');
            span.className = 'page-ellipsis';
            span.textContent = '...';
            pagination.appendChild(span);
        }
    }

    const nextBtn = document.createElement('button');
    nextBtn.className = `page-btn ${page === totalPages ? 'disabled' : ''}`;
    nextBtn.textContent = '下一页';
    nextBtn.onclick = () => { if (page < totalPages) { currentUserPage = page + 1; loadUsers(); } };
    pagination.appendChild(nextBtn);
}

function searchUsers() {
    currentUserPage = 1;
    loadUsers();
}

function filterUsers() {
    currentUserPage = 1;
    loadUsers();
}

async function viewUserDetail(userId) {
    try {
        const response = await fetch(getAdminApiUrl(`/users/${userId}`), {
            headers: getAuthHeaders()
        });

        if (response.ok) {
            const user = await response.json();
            document.getElementById('detailUsername').textContent = user.username;
            document.getElementById('detailEmail').textContent = user.email;
            document.getElementById('detailRole').innerHTML = `<span class="membership-badge ${user.membership_tier}">${getMembershipTierLabel(user.membership_tier)}</span>`;
            document.getElementById('detailStatus').innerHTML = `<span class="status-badge ${user.is_active ? 'active' : 'inactive'}">${user.is_active ? '启用' : '禁用'}</span>`;
            document.getElementById('detailCreatedAt').textContent = formatDate(user.created_at);
            document.getElementById('detailLastLogin').textContent = user.last_login ? formatDate(user.last_login) : '从未登录';

            // 渲染用户密钥
            const keysBody = document.getElementById('userKeysTableBody');
            keysBody.innerHTML = '';
            if (user.keys.length === 0) {
                keysBody.innerHTML = '<tr><td colspan="4" class="empty-cell">暂无密钥</td></tr>';
            } else {
                user.keys.forEach(key => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${key.provider_name}</td>
                        <td>${key.key_name}</td>
                        <td><span class="status-badge ${key.status}">${key.status === 'active' ? '活跃' : '未激活'}</span></td>
                        <td>${formatDate(key.created_at)}</td>
                    `;
                    keysBody.appendChild(tr);
                });
            }

            document.getElementById('userDetailModal').classList.add('active');
            lucide.createIcons();
        }
    } catch (error) {
        console.error('获取用户详情失败:', error);
        showToast('获取用户详情失败', 'error');
    }
}

function closeUserDetailModal() {
    document.getElementById('userDetailModal').classList.remove('active');
}

async function toggleUserRole(userId, currentRole) {
    const newRole = currentRole === 'admin' ? 'user' : 'admin';
    const action = newRole === 'admin' ? '设为管理员' : '取消管理员';
    
    showConfirm(`确定要${action}吗？`, async () => {
        try {
            const headers = getAuthHeaders();
            headers['X-Confirm-Action'] = 'true';
            
            const response = await fetch(getAdminApiUrl(`/users/${userId}/role`), {
                method: 'PUT',
                headers: headers,
                body: JSON.stringify({ role: newRole })
            });

            if (response.ok) {
                showToast(`已${action}`, 'success');
                loadUsers();
            } else {
                const error = await response.json();
                showToast(error.detail || '操作失败', 'error');
            }
        } catch (error) {
            showToast('操作失败', 'error');
        }
    });
}

async function toggleUserStatus(userId, currentActive) {
    const action = currentActive ? '禁用' : '启用';
    
    showConfirm(`确定要${action}该用户吗？`, async () => {
        try {
            const headers = getAuthHeaders();
            headers['X-Confirm-Action'] = 'true';
            
            const response = await fetch(getAdminApiUrl(`/users/${userId}/status`), {
                method: 'PUT',
                headers: headers,
                body: JSON.stringify({ is_active: !currentActive })
            });

            if (response.ok) {
                showToast(`已${action}用户`, 'success');
                loadUsers();
            } else {
                const error = await response.json();
                showToast(error.detail || '操作失败', 'error');
            }
        } catch (error) {
            showToast('操作失败', 'error');
        }
    });
}

// ============ 服务商管理 ============

async function loadProviders() {
    currentPage = 'providers';
    try {
        const response = await fetch(getAdminApiUrl('/providers'), {
            headers: getAuthHeaders()
        });

        if (response.ok) {
            const providers = await response.json();
            renderProvidersTable(providers);
        }
    } catch (error) {
        console.error('加载服务商失败:', error);
        showToast('加载服务商失败', 'error');
    }
}

function renderProvidersTable(providers) {
    const tbody = document.getElementById('providersTableBody');
    tbody.innerHTML = '';

    providers.forEach(p => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${p.id}</td>
            <td>
                <div class="provider-name">
                    <span>${p.display_name}</span>
                    ${p.is_custom ? '<span class="custom-badge">自定义</span>' : ''}
                </div>
            </td>
            <td class="url-cell">${p.base_url}</td>
            <td>${p.model_count}</td>
            <td>${p.key_count}</td>
            <td><span class="status-badge ${p.is_active ? 'active' : 'inactive'}">${p.is_active ? '启用' : '禁用'}</span></td>
            <td>
                <div class="action-buttons">
                    <button class="action-btn ${p.is_active ? 'danger' : 'success'}" onclick="toggleProviderStatus(${p.id}, ${p.is_active})" title="${p.is_active ? '禁用' : '启用'}">
                        <i data-lucide="${p.is_active ? 'toggle-right' : 'toggle-left'}"></i>
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });

    lucide.createIcons();
}

async function toggleProviderStatus(providerId, currentActive) {
    const action = currentActive ? '禁用' : '启用';
    
    showConfirm(`确定要${action}该服务商吗？`, async () => {
        try {
            const response = await fetch(getAdminApiUrl(`/providers/${providerId}/status`), {
                method: 'PUT',
                headers: getAuthHeaders(),
                body: JSON.stringify({ is_active: !currentActive })
            });

            if (response.ok) {
                showToast(`已${action}服务商`, 'success');
                loadProviders();
            } else {
                const error = await response.json();
                showToast(error.detail || '操作失败', 'error');
            }
        } catch (error) {
            showToast('操作失败', 'error');
        }
    });
}

// 添加服务商相关函数
function openAddProviderModal() {
    const modal = document.getElementById('addProviderModal');
    const form = document.getElementById('providerForm');
    if (modal) {
        modal.classList.add('active');
        if (form) form.reset();
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    } else {
        console.error('addProviderModal not found');
    }
}

function closeAddProviderModal() {
    const modal = document.getElementById('addProviderModal');
    const form = document.getElementById('providerForm');
    if (modal) {
        modal.classList.remove('active');
    }
    if (form) {
        form.reset();
    }
}

async function saveProvider() {
    const name = document.getElementById('providerName').value.trim();
    const displayName = document.getElementById('providerDisplayName').value.trim();
    const baseUrl = document.getElementById('providerBaseUrl').value.trim();
    const description = document.getElementById('providerDescription').value.trim();
    const icon = document.getElementById('providerIcon').value;

    if (!name || !displayName || !baseUrl) {
        showToast('请填写必填项', 'error');
        return;
    }

    // 验证标识格式
    if (!/^[a-z0-9_]+$/i.test(name)) {
        showToast('服务商标识只能包含英文字母、数字和下划线', 'error');
        return;
    }

    try {
        const response = await fetch(getAdminApiUrl('/providers'), {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                name: name.toLowerCase(),
                display_name: displayName,
                base_url: baseUrl,
                description: description || null,
                icon: icon
            })
        });

        if (response.ok) {
            showToast('服务商添加成功', 'success');
            closeAddProviderModal();
            loadProviders();
        } else {
            const error = await response.json();
            showToast(error.detail || '添加失败', 'error');
        }
    } catch (error) {
        console.error('添加服务商失败:', error);
        showToast('添加服务商失败', 'error');
    }
}

// ============ 模型管理 ============

async function loadModels() {
    currentPage = 'models';
    const providerId = document.getElementById('modelProviderFilter')?.value || '';

    try {
        // 先加载服务商列表用于筛选
        const providersRes = await fetch(`${API_BASE_URL}/api/keys/providers`, {
            headers: getAuthHeaders()
        });
        if (providersRes.ok) {
            const providers = await providersRes.json();
            const select = document.getElementById('modelProviderFilter');
            select.innerHTML = '<option value="">全部服务商</option>';
            providers.forEach(p => {
                select.innerHTML += `<option value="${p.id}">${p.display_name}</option>`;
            });
            if (providerId) select.value = providerId;
        }

        const params = providerId ? `?provider_id=${providerId}` : '';
        const response = await fetch(getAdminApiUrl(`/models${params}`), {
            headers: getAuthHeaders()
        });

        if (response.ok) {
            const models = await response.json();
            renderModelsTable(models);
        }
    } catch (error) {
        console.error('加载模型失败:', error);
        showToast('加载模型失败', 'error');
    }
}

function filterModels() {
    loadModels();
}

function renderModelsTable(models) {
    const tbody = document.getElementById('modelsTableBody');
    tbody.innerHTML = '';

    if (models.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="empty-cell">暂无模型</td></tr>';
        return;
    }

    models.forEach(m => {
        const tr = document.createElement('tr');
        const categoryMap = {
            'chat': '对话',
            'code': '代码',
            'vision': '视觉',
            'long_context': '长上下文',
            'economy': '经济'
        };
        tr.innerHTML = `
            <td>${m.id}</td>
            <td>${m.provider_name}</td>
            <td><code class="model-id">${m.model_id}</code></td>
            <td>${m.model_name || '-'}</td>
            <td><span class="category-tag">${categoryMap[m.category] || m.category}</span></td>
            <td>${m.context_window || '-'}</td>
            <td>
                <div class="action-buttons">
                    <button class="action-btn danger" onclick="deleteModel(${m.id}, '${m.model_id}')" title="删除">
                        <i data-lucide="trash-2"></i>
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });

    lucide.createIcons();
}

function openAddModelModal() {
    loadProvidersForModal();
    document.getElementById('addModelModal').classList.add('active');
    lucide.createIcons();
}

function closeAddModelModal() {
    document.getElementById('addModelModal').classList.remove('active');
    document.getElementById('modelForm').reset();
}

async function loadProvidersForModal() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/keys/providers`, {
            headers: getAuthHeaders()
        });
        if (response.ok) {
            const providers = await response.json();
            const select = document.getElementById('modelProviderId');
            select.innerHTML = '<option value="">请选择服务商</option>';
            providers.forEach(p => {
                select.innerHTML += `<option value="${p.id}">${p.display_name}</option>`;
            });
        }
    } catch (error) {
        console.error('加载服务商失败:', error);
    }
}

async function saveModel() {
    const providerId = document.getElementById('modelProviderId').value;
    const modelId = document.getElementById('modelId').value.trim();
    const modelName = document.getElementById('modelName').value.trim();
    const category = document.getElementById('modelCategory').value;
    const contextWindow = document.getElementById('modelContext').value.trim();

    if (!providerId || !modelId) {
        showToast('请填写必填项', 'error');
        return;
    }

    try {
        const response = await fetch(getAdminApiUrl('/models'), {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                provider_id: parseInt(providerId),
                model_id: modelId,
                model_name: modelName || modelId,
                category: category,
                context_window: contextWindow || null
            })
        });

        if (response.ok) {
            showToast('模型添加成功', 'success');
            closeAddModelModal();
            loadModels();
        } else {
            const error = await response.json();
            showToast(error.detail || '添加失败', 'error');
        }
    } catch (error) {
        showToast('添加失败', 'error');
    }
}

async function deleteModel(modelId, modelName) {
    showConfirm(`确定要删除模型 "${modelName}" 吗？`, async () => {
        try {
            const headers = getAuthHeaders();
            headers['X-Confirm-Action'] = 'true';
            
            const response = await fetch(getAdminApiUrl(`/models/${modelId}`), {
                method: 'DELETE',
                headers: headers
            });

            if (response.ok) {
                showToast('模型已删除', 'success');
                loadModels();
            } else {
                const error = await response.json();
                showToast(error.detail || '删除失败', 'error');
            }
        } catch (error) {
            showToast('删除失败', 'error');
        }
    });
}

// ============ 配置同步 ============

async function loadConfigStatus() {
    currentPage = 'config';
    try {
        const response = await fetch(getAdminApiUrl('/config/status'), {
            headers: getAuthHeaders()
        });

        if (response.ok) {
            const status = await response.json();
            document.getElementById('configTotalModels').textContent = status.total_models;
            document.getElementById('configTotalProviders').textContent = status.total_providers;
            document.getElementById('configRemoteUrl').textContent = status.remote_url || '未配置';
        }
    } catch (error) {
        console.error('加载配置状态失败:', error);
    }
}

async function syncConfig(source) {
    try {
        showToast('正在同步配置...', 'success');
        
        const response = await fetch(getAdminApiUrl(`/config/sync?source=${source}`), {
            method: 'POST',
            headers: getAuthHeaders()
        });

        if (response.ok) {
            const data = await response.json();
            showToast(data.message, 'success');
            loadConfigStatus();
        } else {
            const error = await response.json();
            showToast(error.detail || '同步失败', 'error');
        }
    } catch (error) {
        console.error('同步配置失败:', error);
        showToast('同步配置失败', 'error');
    }
}

// ============ 确认弹窗 ============

function showConfirm(message, callback) {
    document.getElementById('confirmMessage').textContent = message;
    document.getElementById('confirmModal').classList.add('active');
    confirmCallback = callback;
    lucide.createIcons();
}

function closeConfirmModal() {
    document.getElementById('confirmModal').classList.remove('active');
    confirmCallback = null;
}

function executeConfirm() {
    if (confirmCallback) {
        confirmCallback();
    }
    closeConfirmModal();
}

// ============ 工具函数 ============

function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
}

function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <i data-lucide="${type === 'success' ? 'check-circle' : 'alert-circle'}"></i>
        <span>${message}</span>
    `;
    container.appendChild(toast);
    lucide.createIcons();

    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease-out reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// 角色标签函数
function getRoleLabel(role) {
    const labels = {
        'admin': '管理员',
        'user': '普通用户'
    };
    return labels[role] || '普通用户';
}

// 会员等级相关函数
function getMembershipTierLabel(tier) {
    const labels = {
        'free': '免费版',
        'basic': '基础版',
        'pro': '专业版'
    };
    return labels[tier] || '免费版';
}

function openMembershipUpgradeModal(userId, username, currentTier) {
    // 创建升级弹窗
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.id = 'membershipUpgradeModal';
    modal.innerHTML = `
        <div class="modal modal-lg">
            <div class="modal-header">
                <h2>升级会员</h2>
                <button class="modal-close" onclick="closeMembershipUpgradeModal()">
                    <i data-lucide="x"></i>
                </button>
            </div>
            <div class="modal-body">
                <div class="membership-upgrade-content">
                    <div class="membership-user-info">
                        <h3>用户：${username}</h3>
                        <p>当前版本：<span class="membership-badge ${currentTier}">${getMembershipTierLabel(currentTier)}</span></p>
                    </div>
                    
                    <div class="membership-tier-grid">
                        <div class="membership-tier ${currentTier === 'free' ? 'selected' : ''}">
                            <div class="tier-header">
                                <h4>免费版</h4>
                                <span class="tier-price">免费</span>
                            </div>
                            <ul class="tier-features">
                                <li><i data-lucide="check"></i> 基础 API 密钥管理</li>
                                <li><i data-lucide="check"></i> 5 个密钥</li>
                                <li><i data-lucide="check"></i> 基础模型支持</li>
                                <li><i data-lucide="x"></i> 无优先支持</li>
                            </ul>
                            <button class="btn-secondary" disabled>当前版本</button>
                        </div>
                        
                        <div class="membership-tier ${currentTier === 'basic' ? 'selected' : ''}">
                            <div class="tier-header">
                                <h4>基础版</h4>
                                <span class="tier-price">¥19/月</span>
                            </div>
                            <ul class="tier-features">
                                <li><i data-lucide="check"></i> 免费版所有功能</li>
                                <li><i data-lucide="check"></i> 20 个密钥</li>
                                <li><i data-lucide="check"></i> 所有模型支持</li>
                                <li><i data-lucide="check"></i> 优先技术支持</li>
                            </ul>
                            <button class="btn-primary" onclick="upgradeMembership(${userId}, 'basic')">升级到基础版</button>
                        </div>
                        
                        <div class="membership-tier ${currentTier === 'pro' ? 'selected' : ''}">
                            <div class="tier-header">
                                <h4>专业版</h4>
                                <span class="tier-price">¥49/月</span>
                            </div>
                            <ul class="tier-features">
                                <li><i data-lucide="check"></i> 基础版所有功能</li>
                                <li><i data-lucide="check"></i> 无限密钥</li>
                                <li><i data-lucide="check"></i> 高级模型支持</li>
                                <li><i data-lucide="check"></i> 24/7 专属支持</li>
                            </ul>
                            <button class="btn-primary" onclick="upgradeMembership(${userId}, 'pro')">升级到专业版</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    lucide.createIcons();
}

function closeMembershipUpgradeModal() {
    const modal = document.getElementById('membershipUpgradeModal');
    if (modal) {
        modal.remove();
    }
}

async function upgradeMembership(userId, tier) {
    try {
        const headers = getAuthHeaders();
        headers['X-Confirm-Action'] = 'true';
        
        const response = await fetch(getAdminApiUrl(`/users/${userId}/membership`), {
            method: 'PUT',
            headers: headers,
            body: JSON.stringify({ membership_tier: tier })
        });
        
        if (response.ok) {
            closeMembershipUpgradeModal();
            showToast(`会员升级成功：${getMembershipTierLabel(tier)}`, 'success');
            loadUsers(); // 刷新用户列表
        } else {
            const data = await response.json();
            showToast(data.message || '升级失败', 'error');
        }
    } catch (error) {
        console.error('升级会员失败:', error);
        showToast('升级失败', 'error');
    }
}

function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('collapsed');
}

function handleLogout() {
    localStorage.removeItem('token');
    window.location.href = 'index.html';
}

// ============ 日志审计 ============

async function loadLogs() {
    try {
        const params = new URLSearchParams();
        params.append('page', logsPage);
        params.append('page_size', logsPageSize);
        
        const userId = document.getElementById('logUserId').value;
        if (userId) params.append('user_id', userId);
        
        const action = document.getElementById('logAction').value;
        if (action) params.append('action', action);
        
        const resourceType = document.getElementById('logResourceType').value;
        if (resourceType) params.append('resource_type', resourceType);
        
        const status = document.getElementById('logStatus').value;
        if (status) params.append('status', status);
        
        const startDate = document.getElementById('logStartDate').value;
        if (startDate) params.append('start_date', startDate);
        
        const endDate = document.getElementById('logEndDate').value;
        if (endDate) params.append('end_date', endDate);
        
        const response = await fetch(getAdminApiUrl(`/logs?${params}`), {
            headers: getAuthHeaders()
        });
        
        if (!response.ok) {
            throw new Error('加载日志失败');
        }
        
        const result = await response.json();
        logsData = result.logs || [];
        
        renderLogsTable();
        updateLogPagination(result);
    } catch (error) {
        console.error('加载日志失败:', error);
        showToast('加载日志失败', 'error');
    }
}

function renderLogsTable() {
    const tbody = document.getElementById('logsTableBody');
    tbody.innerHTML = '';
    
    if (logsData.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center text-muted">暂无日志数据</td>
            </tr>
        `;
        return;
    }
    
    logsData.forEach(log => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${formatDateTime(log.created_at)}</td>
            <td>${log.username || '-'}</td>
            <td>
                <span class="badge badge-info">${log.action}</span>
            </td>
            <td>${log.resource_type || '-'}</td>
            <td>${log.resource_name || '-'}</td>
            <td>${log.ip_address || '-'}</td>
            <td>
                <span class="badge ${log.status === 'success' ? 'badge-success' : 'badge-danger'}">
                    ${log.status === 'success' ? '成功' : '失败'}
                </span>
            </td>
            <td>
                <button class="btn-small" onclick="viewLogDetails('${escapeHtml(JSON.stringify(log))}')" title="查看详情">
                    <i data-lucide="eye"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function updateLogPagination(result) {
    const totalPages = Math.ceil(result.total / logsPageSize);
    const prevBtn = document.getElementById('logsPrevBtn');
    const nextBtn = document.getElementById('logsNextBtn');
    const pageInfo = document.getElementById('logsPageInfo');
    
    prevBtn.disabled = logsPage <= 1;
    nextBtn.disabled = logsPage >= totalPages;
    pageInfo.textContent = `第 ${logsPage} 页，共 ${totalPages} 页`;
}

function previousLogsPage() {
    if (logsPage > 1) {
        logsPage--;
        loadLogs();
    }
}

function nextLogsPage() {
    const totalPages = Math.ceil(logsData.length / logsPageSize);
    if (logsPage < totalPages) {
        logsPage++;
        loadLogs();
    }
}

async function loadLogFilters() {
    try {
        const [usersResponse, actionsResponse, resourceTypesResponse] = await Promise.all([
            fetch(getAdminApiUrl('/logs/users'), { headers: getAuthHeaders() }),
            fetch(getAdminApiUrl('/logs/actions'), { headers: getAuthHeaders() }),
            fetch(getAdminApiUrl('/logs/resource-types'), { headers: getAuthHeaders() })
        ]);
        
        if (!usersResponse.ok || !actionsResponse.ok || !resourceTypesResponse.ok) {
            throw new Error('加载筛选条件失败');
        }
        
        const [users, actions, resourceTypes] = await Promise.all([
            usersResponse.json(),
            actionsResponse.json(),
            resourceTypesResponse.json()
        ]);
        
        // 填充用户下拉框
        const userSelect = document.getElementById('logUserId');
        userSelect.innerHTML = '<option value="">全部用户</option>';
        users.forEach(user => {
            const option = document.createElement('option');
            option.value = user.id;
            option.textContent = user.username;
            userSelect.appendChild(option);
        });
        
        // 填充操作类型下拉框
        const actionSelect = document.getElementById('logAction');
        actionSelect.innerHTML = '<option value="">全部操作</option>';
        actions.forEach(action => {
            const option = document.createElement('option');
            option.value = action;
            option.textContent = action;
            actionSelect.appendChild(option);
        });
        
        // 填充资源类型下拉框
        const resourceTypeSelect = document.getElementById('logResourceType');
        resourceTypeSelect.innerHTML = '<option value="">全部资源</option>';
        resourceTypes.forEach(rt => {
            const option = document.createElement('option');
            option.value = rt;
            option.textContent = rt;
            resourceTypeSelect.appendChild(option);
        });
    } catch (error) {
        console.error('加载筛选条件失败:', error);
    }
}

function resetLogFilters() {
    document.getElementById('logUserId').value = '';
    document.getElementById('logAction').value = '';
    document.getElementById('logResourceType').value = '';
    document.getElementById('logStatus').value = '';
    document.getElementById('logStartDate').value = '';
    document.getElementById('logEndDate').value = '';
    logsPage = 1;
    loadLogs();
}

function exportLogs() {
    if (logsData.length === 0) {
        showToast('没有数据可导出', 'warning');
        return;
    }
    
    const headers = ['时间', '用户', '操作', '资源类型', '资源名称', 'IP地址', '状态', '错误信息'];
    let csv = headers.join(',') + '\n';
    
    logsData.forEach(log => {
        const row = [
            formatDateTime(log.created_at),
            log.username || '',
            log.action,
            log.resource_type || '',
            log.resource_name || '',
            log.ip_address || '',
            log.status === 'success' ? '成功' : '失败',
            log.error_message || ''
        ].map(cell => `"${cell}"`).join(',');
        csv += row + '\n';
    });
    
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `logs_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function viewLogDetails(logStr) {
    const log = JSON.parse(logStr);
    let details = '<div class="log-details">';
    details += `<p><strong>操作:</strong> ${escapeHtml(log.action)}</p>`;
    details += `<p><strong>用户:</strong> ${escapeHtml(log.username || '-')}</p>`;
    details += `<p><strong>资源类型:</strong> ${escapeHtml(log.resource_type || '-')}</p>`;
    details += `<p><strong>资源ID:</strong> ${log.resource_id || '-'}</p>`;
    details += `<p><strong>资源名称:</strong> ${escapeHtml(log.resource_name || '-')}</p>`;
    details += `<p><strong>IP地址:</strong> ${escapeHtml(log.ip_address || '-')}</p>`;
    details += `<p><strong>状态:</strong> <span class="badge ${log.status === 'success' ? 'badge-success' : 'badge-danger'}">${log.status === 'success' ? '成功' : '失败'}</span></p>`;
    if (log.error_message) {
        details += `<p><strong>错误信息:</strong> <span class="text-danger">${escapeHtml(log.error_message)}</span></p>`;
    }
    if (log.details) {
        details += `<p><strong>详情:</strong></p><pre class="log-details-pre">${escapeHtml(JSON.stringify(log.details, null, 2))}</pre>`;
    }
    details += '</div>';
    
    showToast(details, 'info');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDateTime(isoString) {
    const date = new Date(isoString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
}

// ============ 高危操作确认 ============

function showHighRiskConfirm(action, callback) {
    highRiskConfirmAction = action;
    confirmCallback = callback;
    
    const modal = document.getElementById('confirmModal');
    const title = document.getElementById('confirmTitle');
    const message = document.getElementById('confirmMessage');
    
    title.textContent = '高危操作确认';
    message.innerHTML = `
        <div class="warning-icon">
            <i data-lucide="alert-triangle"></i>
        </div>
        <p>您即将执行高危操作：<strong>${escapeHtml(action)}</strong></p>
        <p class="text-muted">此操作不可撤销，请确认是否继续。</p>
    `;
    
    document.getElementById('confirmBtn').textContent = '确认执行';
    document.getElementById('confirmBtn').className = 'btn-danger';
    
    modal.style.display = 'flex';
    lucide.createIcons();
}

function closeHighRiskConfirm() {
    const modal = document.getElementById('confirmModal');
    modal.style.display = 'none';
    highRiskConfirmAction = null;
    confirmCallback = null;
}

function executeHighRiskConfirm() {
    if (confirmCallback) {
        confirmCallback();
    }
    closeHighRiskConfirm();
}

// ============ 用户管理增强 ============

async function deleteUser(userId, username) {
    showHighRiskConfirm(`删除用户 ${username}`, async () => {
        try {
            const headers = getAuthHeaders();
            headers['X-Confirm-Action'] = 'true';
            
            const response = await fetch(getAdminApiUrl(`/users/${userId}`), {
                method: 'DELETE',
                headers: headers
            });
            
            if (!response.ok) {
                throw new Error('删除用户失败');
            }
            
            showToast('用户已删除', 'success');
            loadUsers();
        } catch (error) {
            console.error('删除用户失败:', error);
            showToast(error.message || '删除用户失败', 'error');
        }
    });
}

async function updateUserRole(userId, currentRole) {
    const newRole = currentRole === 'admin' ? 'user' : 'admin';
    const action = currentRole === 'admin' ? '降级为普通用户' : '提升为管理员';
    
    showHighRiskConfirm(`修改用户角色 - ${action}`, async () => {
        try {
            const headers = getAuthHeaders();
            headers['X-Confirm-Action'] = 'true';
            
            const response = await fetch(getAdminApiUrl(`/users/${userId}/role`), {
                method: 'PUT',
                headers: headers,
                body: JSON.stringify({ role: newRole })
            });
            
            if (!response.ok) {
                throw new Error('更新用户角色失败');
            }
            
            showToast(`用户角色已更新为 ${newRole}`, 'success');
            loadUsers();
        } catch (error) {
            console.error('更新用户角色失败:', error);
            showToast(error.message || '更新用户角色失败', 'error');
        }
    });
}

async function toggleUserStatus(userId, username, isActive) {
    const action = isActive ? '禁用' : '启用';
    
    showHighRiskConfirm(`禁用用户 ${username}`, async () => {
        try {
            const headers = getAuthHeaders();
            headers['X-Confirm-Action'] = 'true';
            
            const response = await fetch(getAdminApiUrl(`/users/${userId}/status`), {
                method: 'PUT',
                headers: headers,
                body: JSON.stringify({ is_active: !isActive })
            });
            
            if (!response.ok) {
                throw new Error('更新用户状态失败');
            }
            
            showToast(`用户已${action === '禁用' ? '禁用' : '启用'}`, 'success');
            loadUsers();
        } catch (error) {
            console.error('更新用户状态失败:', error);
            showToast(error.message || '更新用户状态失败', 'error');
        }
    });
}

// ============ 服务商管理增强 ============

async function deleteProvider(providerId, providerName) {
    showHighRiskConfirm(`删除服务商 ${providerName}`, async () => {
        try {
            const headers = getAuthHeaders();
            headers['X-Confirm-Action'] = 'true';
            
            const response = await fetch(getAdminApiUrl(`/providers/${providerId}`), {
                method: 'DELETE',
                headers: headers
            });
            
            if (!response.ok) {
                throw new Error('删除服务商失败');
            }
            
            showToast('服务商已删除', 'success');
            loadProviders();
        } catch (error) {
            console.error('删除服务商失败:', error);
            showToast(error.message || '删除服务商失败', 'error');
        }
    });
}

// ============ 模型管理增强 ============

async function deleteModel(modelId, modelName) {
    showHighRiskConfirm(`删除模型 ${modelName}`, async () => {
        try {
            const headers = getAuthHeaders();
            headers['X-Confirm-Action'] = 'true';
            
            const response = await fetch(getAdminApiUrl(`/models/${modelId}`), {
                method: 'DELETE',
                headers: headers
            });
            
            if (!response.ok) {
                throw new Error('删除模型失败');
            }
            
            showToast('模型已删除', 'success');
            loadModels();
        } catch (error) {
            console.error('删除模型失败:', error);
            showToast(error.message || '删除模型失败', 'error');
        }
    });
}
