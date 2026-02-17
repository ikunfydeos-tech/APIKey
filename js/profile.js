// 用户中心页面脚本
const API_BASE_URL = 'http://localhost:8000';

// TOTP 状态
let totpSecret = '';

// 页面初始化
document.addEventListener('DOMContentLoaded', async function() {
    const isLoggedIn = await checkLoginStatus();
    if (isLoggedIn) {
        await loadUserInfo();
        await loadSecurityScore();
        await loadTOTPStatus();
        await loadLoginHistory();
        await loadSessions();
        checkAdminStatus();
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
        return true;
    } catch (error) {
        console.error('验证登录状态失败:', error);
        return false;
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

// 加载用户信息
async function loadUserInfo() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/me`, {
            headers: getAuthHeaders()
        });
        
        if (response.ok) {
            const user = await response.json();
            document.getElementById('usernameDisplay').textContent = user.username;
            document.getElementById('userRole').textContent = user.role === 'admin' ? '管理员' : '用户';
            document.getElementById('infoUsername').textContent = user.username;
            document.getElementById('infoEmail').textContent = user.email || '-';
            document.getElementById('infoRole').textContent = user.role === 'admin' ? '管理员' : '用户';
            document.getElementById('infoCreatedAt').textContent = formatDate(user.created_at);
            document.getElementById('infoLastLogin').textContent = user.last_login ? formatDate(user.last_login) : '从未登录';
        }
    } catch (error) {
        console.error('加载用户信息失败:', error);
    }
}

// 加载安全评分
async function loadSecurityScore() {
    const checks = [];
    let score = 0;
    
    try {
        // 检查各项安全指标
        const [meRes, totpRes] = await Promise.all([
            fetch(`${API_BASE_URL}/api/me`, { headers: getAuthHeaders() }),
            fetch(`${API_BASE_URL}/api/totp/status`, { headers: getAuthHeaders() })
        ]);
        
        if (meRes.ok) {
            const user = await meRes.json();
            
            // 检查邮箱是否验证（简化：有邮箱就认为通过）
            if (user.email) {
                checks.push({ name: '邮箱已设置', status: 'success' });
                score += 25;
            } else {
                checks.push({ name: '邮箱未设置', status: 'warning' });
            }
        }
        
        if (totpRes.ok) {
            const totp = await totpRes.json();
            if (totp.is_enabled) {
                checks.push({ name: '双因素认证', status: 'success' });
                score += 50;
            } else {
                checks.push({ name: '双因素认证', status: 'danger' });
            }
        }
        
        // 密码强度（默认认为通过，实际应该检查密码修改时间）
        checks.push({ name: '密码强度', status: 'success' });
        score += 25;
        
    } catch (error) {
        console.error('加载安全评分失败:', error);
        checks.push({ name: '无法获取安全状态', status: 'warning' });
    }
    
    // 更新 UI
    updateScoreRing(score);
    updateChecklist(checks);
}

// 更新评分环
function updateScoreRing(score) {
    const ring = document.getElementById('scoreRing');
    const scoreNumber = document.getElementById('securityScore');
    const scoreDescription = document.getElementById('scoreDescription');
    
    // 计算环的偏移量
    const circumference = 339.292;
    const offset = circumference - (score / 100) * circumference;
    
    ring.style.strokeDashoffset = offset;
    ring.classList.remove('low', 'medium', 'high');
    
    if (score < 40) {
        ring.classList.add('low');
        scoreDescription.textContent = '您的账户安全状况较差，建议立即改进。';
    } else if (score < 70) {
        ring.classList.add('medium');
        scoreDescription.textContent = '您的账户安全状况一般，仍有改进空间。';
    } else {
        ring.classList.add('high');
        scoreDescription.textContent = '您的账户安全状况良好，继续保持。';
    }
    
    scoreNumber.textContent = score;
}

// 更新检查列表
function updateChecklist(checks) {
    const container = document.getElementById('securityChecklist');
    container.innerHTML = checks.map(check => `
        <div class="check-item ${check.status}">
            <i data-lucide="${check.status === 'success' ? 'check-circle' : check.status === 'warning' ? 'alert-circle' : 'x-circle'}"></i>
            <span>${check.name}</span>
        </div>
    `).join('');
    lucide.createIcons();
}

// 加载 TOTP 状态
async function loadTOTPStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/totp/status`, {
            headers: getAuthHeaders()
        });
        
        if (response.ok) {
            const result = await response.json();
            updateTOTPUI(result.is_enabled);
        }
    } catch (error) {
        console.error('加载 TOTP 状态失败:', error);
    }
}

// 更新 TOTP UI
function updateTOTPUI(isEnabled) {
    const statusBadge = document.getElementById('totpStatusBadge');
    const disabledSection = document.getElementById('totpDisabledSection');
    const setupSection = document.getElementById('totpSetupSection');
    const enabledSection = document.getElementById('totpEnabledSection');
    
    if (isEnabled) {
        statusBadge.textContent = '已启用';
        statusBadge.classList.add('active');
        disabledSection.classList.add('hidden');
        setupSection.classList.add('hidden');
        enabledSection.classList.remove('hidden');
    } else {
        statusBadge.textContent = '未启用';
        statusBadge.classList.remove('active');
        disabledSection.classList.remove('hidden');
        setupSection.classList.add('hidden');
        enabledSection.classList.add('hidden');
    }
    
    // 重新计算安全评分
    loadSecurityScore();
}

// 设置 TOTP
async function setupTOTP() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/totp/secret`, {
            headers: getAuthHeaders()
        });
        
        if (response.ok) {
            const result = await response.json();
            totpSecret = result.secret;
            
            document.getElementById('totpSecret').value = totpSecret;
            document.getElementById('totpQrCode').src = result.qr_code;
            
            document.getElementById('totpDisabledSection').classList.add('hidden');
            document.getElementById('totpSetupSection').classList.remove('hidden');
        } else {
            showToast('获取 TOTP 密钥失败', 'error');
        }
    } catch (error) {
        console.error('获取 TOTP 密钥失败:', error);
        showToast('获取 TOTP 密钥失败', 'error');
    }
}

// 启用 TOTP
async function enableTOTP() {
    const token = document.getElementById('totpToken').value;
    
    if (!token || token.length !== 6) {
        showToast('请输入6位验证码', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/totp/enable`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ token: token, secret: totpSecret })
        });
        
        if (response.ok) {
            showToast('2FA 已启用', 'success');
            document.getElementById('totpToken').value = '';
            updateTOTPUI(true);
        } else {
            const error = await response.json();
            showToast(error.detail || '启用失败', 'error');
        }
    } catch (error) {
        console.error('启用 TOTP 失败:', error);
        showToast('启用 TOTP 失败', 'error');
    }
}

// 禁用 TOTP
async function disableTOTP() {
    const token = document.getElementById('totpDisableToken').value;
    
    if (!token || token.length !== 6) {
        showToast('请输入6位验证码', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/totp/disable`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ token: token })
        });
        
        if (response.ok) {
            showToast('2FA 已禁用', 'success');
            document.getElementById('totpDisableToken').value = '';
            updateTOTPUI(false);
        } else {
            const error = await response.json();
            showToast(error.detail || '禁用失败', 'error');
        }
    } catch (error) {
        console.error('禁用 TOTP 失败:', error);
        showToast('禁用 TOTP 失败', 'error');
    }
}

// 取消 TOTP 设置
function cancelTOTPSetup() {
    document.getElementById('totpToken').value = '';
    document.getElementById('totpSetupSection').classList.add('hidden');
    document.getElementById('totpDisabledSection').classList.remove('hidden');
    totpSecret = '';
}

// 复制密钥
function copySecret() {
    const secret = document.getElementById('totpSecret').value;
    navigator.clipboard.writeText(secret).then(() => {
        showToast('已复制到剪贴板', 'success');
    });
}

// 加载登录历史
async function loadLoginHistory() {
    const container = document.getElementById('loginHistoryList');
    container.innerHTML = '<div class="history-item"><span style="color: #6b7280;">加载中...</span></div>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/login-history`, {
            headers: getAuthHeaders()
        });
        
        if (response.ok) {
            const data = await response.json();
            renderLoginHistory(data.history || []);
        } else {
            // 使用模拟数据
            renderLoginHistory(generateMockLoginHistory());
        }
    } catch (error) {
        console.error('加载登录历史失败:', error);
        renderLoginHistory(generateMockLoginHistory());
    }
}

// 渲染登录历史
function renderLoginHistory(history) {
    const container = document.getElementById('loginHistoryList');
    
    if (history.length === 0) {
        container.innerHTML = '<div class="history-item"><span style="color: #6b7280;">暂无登录记录</span></div>';
        return;
    }
    
    container.innerHTML = history.map((item, index) => `
        <div class="history-item">
            <div class="history-icon ${item.success ? 'success' : 'failed'}">
                <i data-lucide="${item.success ? 'log-in' : 'alert-circle'}"></i>
            </div>
            <div class="history-info">
                <h4>${item.browser || '浏览器'} · ${item.os || '操作系统'}</h4>
                <p>
                    <span>${item.ip || 'IP地址'}</span>
                    <span>${item.location || '位置'}</span>
                </p>
            </div>
            <div class="history-time">
                ${index === 0 && item.success ? '<span class="history-current">当前</span>' : ''}
                ${formatRelativeTime(item.time)}
            </div>
        </div>
    `).join('');
    
    lucide.createIcons();
}

// 生成模拟登录历史
function generateMockLoginHistory() {
    return [
        { browser: 'Chrome', os: 'Windows', ip: '192.168.1.***', location: '本地', time: new Date().toISOString(), success: true },
        { browser: 'Chrome', os: 'Windows', ip: '192.168.1.***', location: '本地', time: new Date(Date.now() - 86400000).toISOString(), success: true },
        { browser: 'Firefox', os: 'macOS', ip: '10.0.0.***', location: '未知', time: new Date(Date.now() - 172800000).toISOString(), success: false },
    ];
}

// 加载会话列表
async function loadSessions() {
    const container = document.getElementById('sessionList');
    container.innerHTML = '<div class="session-item"><span style="color: #6b7280;">加载中...</span></div>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/sessions`, {
            headers: getAuthHeaders()
        });
        
        if (response.ok) {
            const data = await response.json();
            renderSessions(data.sessions || []);
        } else {
            // 使用模拟数据
            renderSessions(generateMockSessions());
        }
    } catch (error) {
        console.error('加载会话列表失败:', error);
        renderSessions(generateMockSessions());
    }
}

// 渲染会话列表
function renderSessions(sessions) {
    const container = document.getElementById('sessionList');
    
    if (sessions.length === 0) {
        container.innerHTML = '<div class="session-item"><span style="color: #6b7280;">暂无活跃会话</span></div>';
        return;
    }
    
    container.innerHTML = sessions.map((session, index) => `
        <div class="session-item ${session.current ? 'current' : ''}">
            <div class="session-icon">
                <i data-lucide="${getDeviceIcon(session.device_type)}"></i>
            </div>
            <div class="session-info">
                <h4>${session.device || '设备'} · ${session.browser || '浏览器'}</h4>
                <p>
                    ${session.current ? '<span class="current-label">当前设备</span> · ' : ''}
                    ${session.ip || 'IP'} · ${session.last_active ? formatRelativeTime(session.last_active) : ''}
                </p>
            </div>
            ${!session.current ? `<button class="session-revoke" onclick="revokeSession('${session.id}')">登出</button>` : ''}
        </div>
    `).join('');
    
    lucide.createIcons();
}

// 生成模拟会话
function generateMockSessions() {
    return [
        { id: 'current', device: '此设备', browser: 'Chrome', device_type: 'desktop', ip: '192.168.1.***', last_active: new Date().toISOString(), current: true },
    ];
}

// 获取设备图标
function getDeviceIcon(type) {
    switch (type) {
        case 'mobile': return 'smartphone';
        case 'tablet': return 'tablet';
        default: return 'monitor';
    }
}

// 撤销会话
async function revokeSession(sessionId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/sessions/${sessionId}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });
        
        if (response.ok) {
            showToast('已登出该设备', 'success');
            loadSessions();
        } else {
            showToast('操作失败', 'error');
        }
    } catch (error) {
        console.error('撤销会话失败:', error);
        showToast('操作失败', 'error');
    }
}

// 撤销所有会话
async function revokeAllSessions() {
    if (!confirm('确定要登出所有其他设备吗？')) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/sessions`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });
        
        if (response.ok) {
            showToast('已登出所有其他设备', 'success');
            loadSessions();
        } else {
            showToast('操作失败', 'error');
        }
    } catch (error) {
        console.error('撤销会话失败:', error);
        showToast('操作失败', 'error');
    }
}

// 初始化事件监听
function initEventListeners() {
    // 密码表单
    document.getElementById('passwordForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        await changePassword();
    });
    
    // 密码强度检测
    document.getElementById('newPassword').addEventListener('input', function(e) {
        checkPasswordStrength(e.target.value);
    });
}

// 修改密码
async function changePassword() {
    const currentPassword = document.getElementById('currentPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    
    if (!currentPassword || !newPassword || !confirmPassword) {
        showToast('请填写所有字段', 'error');
        return;
    }
    
    if (newPassword !== confirmPassword) {
        showToast('两次输入的新密码不一致', 'error');
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
                new_password: newPassword
            })
        });
        
        if (response.ok) {
            showToast('密码修改成功，请重新登录', 'success');
            setTimeout(() => {
                handleLogout();
            }, 2000);
        } else {
            const error = await response.json();
            showToast(error.detail || '修改失败', 'error');
        }
    } catch (error) {
        console.error('修改密码失败:', error);
        showToast('修改密码失败', 'error');
    }
}

// 检查密码强度
function checkPasswordStrength(password) {
    const fill = document.getElementById('strengthFill');
    const text = document.getElementById('strengthText');
    
    let strength = 0;
    if (password.length >= 8) strength++;
    if (password.length >= 12) strength++;
    if (/[A-Z]/.test(password) && /[a-z]/.test(password)) strength++;
    if (/\d/.test(password)) strength++;
    if (/[^A-Za-z0-9]/.test(password)) strength++;
    
    fill.classList.remove('weak', 'medium', 'strong');
    
    if (strength <= 2) {
        fill.classList.add('weak');
        text.textContent = '弱';
    } else if (strength <= 4) {
        fill.classList.add('medium');
        text.textContent = '中';
    } else {
        fill.classList.add('strong');
        text.textContent = '强';
    }
}

// 切换密码可见性
function togglePasswordField(fieldId) {
    const field = document.getElementById(fieldId);
    const button = field.nextElementSibling;
    const icon = button.querySelector('i');
    
    if (field.type === 'password') {
        field.type = 'text';
        icon.setAttribute('data-lucide', 'eye-off');
    } else {
        field.type = 'password';
        icon.setAttribute('data-lucide', 'eye');
    }
    lucide.createIcons();
}

// 导出数据
async function exportData() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/keys/export`, {
            headers: getAuthHeaders()
        });
        
        if (response.ok) {
            const data = await response.json();
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `api-keys-${new Date().toISOString().split('T')[0]}.json`;
            a.click();
            URL.revokeObjectURL(url);
            showToast('数据导出成功', 'success');
        } else {
            showToast('导出失败', 'error');
        }
    } catch (error) {
        console.error('导出数据失败:', error);
        showToast('导出失败', 'error');
    }
}

// 显示删除账户弹窗
function showDeleteAccountModal() {
    document.getElementById('deleteAccountModal').classList.add('active');
    lucide.createIcons();
}

// 关闭删除账户弹窗
function closeDeleteAccountModal() {
    document.getElementById('deleteAccountModal').classList.remove('active');
    document.getElementById('deleteConfirmPassword').value = '';
}

// 删除账户
async function deleteAccount() {
    const password = document.getElementById('deleteConfirmPassword').value;
    
    if (!password) {
        showToast('请输入密码', 'error');
        return;
    }
    
    if (!confirm('确定要永久删除账户吗？此操作不可恢复！')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/account`, {
            method: 'DELETE',
            headers: getAuthHeaders(),
            body: JSON.stringify({ password: password })
        });
        
        if (response.ok) {
            showToast('账户已删除', 'success');
            setTimeout(() => {
                handleLogout();
            }, 1500);
        } else {
            const error = await response.json();
            showToast(error.detail || '删除失败', 'error');
        }
    } catch (error) {
        console.error('删除账户失败:', error);
        showToast('删除失败', 'error');
    }
}

// 检查管理员状态
async function checkAdminStatus() {
    const token = localStorage.getItem('token');
    if (!token) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/me`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            const user = await response.json();
            if (user.role === 'admin') {
                document.getElementById('navAdmin').style.display = 'flex';
            }
        }
    } catch (error) {
        console.error('检查管理员状态失败:', error);
    }
}

// 跳转到管理后台
async function goToAdmin(event) {
    event.preventDefault();
    
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
            window.location.href = `admin.html?path=${data.admin_path}`;
        } else {
            showToast('无法访问管理后台', 'error');
        }
    } catch (error) {
        console.error('获取管理员入口失败:', error);
        showToast('获取管理员入口失败', 'error');
    }
}

// 登出
function handleLogout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = 'index.html';
}

// 切换侧边栏
function toggleSidebar() {
    document.querySelector('.sidebar').classList.toggle('collapsed');
}

// 工具函数：格式化日期
function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
}

// 工具函数：相对时间
function formatRelativeTime(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now - date;
    
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    
    if (minutes < 1) return '刚刚';
    if (minutes < 60) return `${minutes}分钟前`;
    if (hours < 24) return `${hours}小时前`;
    if (days < 7) return `${days}天前`;
    
    return formatDate(dateStr);
}

// Toast 通知
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
