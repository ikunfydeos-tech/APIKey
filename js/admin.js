// 管理后台 JavaScript
const API_BASE_URL = 'http://localhost:8000';

// 状态管理
let currentPage = 'dashboard';
let currentUserPage = 1;
let usersPageSize = 20;
let registrationChart = null;
let providerChart = null;
let confirmCallback = null;

// ============ 初始化 ============

document.addEventListener('DOMContentLoaded', async function() {
    await checkAdminStatus();
    await loadDashboardData();
});

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

// ============ 页面切换 ============

function switchToDashboard() {
    hideAllPages();
    document.getElementById('dashboardPage').style.display = 'block';
    document.getElementById('currentPageName').textContent = '数据概览';
    setActiveNav('navDashboard');
    loadDashboardData();
}

function switchToUsers() {
    hideAllPages();
    document.getElementById('usersPage').style.display = 'block';
    document.getElementById('currentPageName').textContent = '用户管理';
    setActiveNav('navUsers');
    loadUsers();
}

function switchToProviders() {
    hideAllPages();
    document.getElementById('providersPage').style.display = 'block';
    document.getElementById('currentPageName').textContent = '服务商管理';
    setActiveNav('navProviders');
    loadProviders();
}

function switchToModels() {
    hideAllPages();
    document.getElementById('modelsPage').style.display = 'block';
    document.getElementById('currentPageName').textContent = '模型管理';
    setActiveNav('navModels');
    loadModels();
}

function switchToConfig() {
    hideAllPages();
    document.getElementById('configPage').style.display = 'block';
    document.getElementById('currentPageName').textContent = '配置同步';
    setActiveNav('navConfig');
    loadConfigStatus();
}

function hideAllPages() {
    document.getElementById('dashboardPage').style.display = 'none';
    document.getElementById('usersPage').style.display = 'none';
    document.getElementById('providersPage').style.display = 'none';
    document.getElementById('modelsPage').style.display = 'none';
    document.getElementById('configPage').style.display = 'none';
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
    }
}

// ============ 数据概览 ============

async function loadDashboardData() {
    currentPage = 'dashboard';
    try {
        // 加载统计数据
        const [statsRes, providerStatsRes, trendRes] = await Promise.all([
            fetch(`${API_BASE_URL}/api/admin/stats/overview`, { headers: getAuthHeaders() }),
            fetch(`${API_BASE_URL}/api/admin/stats/providers`, { headers: getAuthHeaders() }),
            fetch(`${API_BASE_URL}/api/admin/stats/registration-trend?days=7`, { headers: getAuthHeaders() })
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

        const response = await fetch(`${API_BASE_URL}/api/admin/users?${params}`, {
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
            <td><span class="role-badge ${user.role}">${user.role === 'admin' ? '管理员' : '用户'}</span></td>
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
        const response = await fetch(`${API_BASE_URL}/api/admin/users/${userId}`, {
            headers: getAuthHeaders()
        });

        if (response.ok) {
            const user = await response.json();
            document.getElementById('detailUsername').textContent = user.username;
            document.getElementById('detailEmail').textContent = user.email;
            document.getElementById('detailRole').innerHTML = `<span class="role-badge ${user.role}">${user.role === 'admin' ? '管理员' : '用户'}</span>`;
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
            const response = await fetch(`${API_BASE_URL}/api/admin/users/${userId}/role`, {
                method: 'PUT',
                headers: getAuthHeaders(),
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
            const response = await fetch(`${API_BASE_URL}/api/admin/users/${userId}/status`, {
                method: 'PUT',
                headers: getAuthHeaders(),
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
        const response = await fetch(`${API_BASE_URL}/api/admin/providers`, {
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
            const response = await fetch(`${API_BASE_URL}/api/admin/providers/${providerId}/status`, {
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
        const response = await fetch(`${API_BASE_URL}/api/admin/models${params}`, {
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
        const response = await fetch(`${API_BASE_URL}/api/admin/models`, {
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
            const response = await fetch(`${API_BASE_URL}/api/admin/models/${modelId}`, {
                method: 'DELETE',
                headers: getAuthHeaders()
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
        const response = await fetch(`${API_BASE_URL}/api/admin/config/status`, {
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
        
        const response = await fetch(`${API_BASE_URL}/api/admin/config/sync?source=${source}`, {
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

function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('collapsed');
}

function handleLogout() {
    localStorage.removeItem('token');
    window.location.href = 'index.html';
}
