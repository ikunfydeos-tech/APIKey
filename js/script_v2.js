// 重构版登录脚本 - 强制TOTP

const API_BASE_URL = 'http://localhost:8000';

// DOM元素
const loginForm = document.getElementById('loginForm');
const loadingOverlay = document.getElementById('loadingOverlay');
const notificationContainer = document.getElementById('notificationContainer');

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化 Lucide 图标
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
    
    initLoginForm();
    
    // 检查是否已登录
    const token = localStorage.getItem('token');
    if (token) {
        // 验证token有效性
        validateToken(token);
    }
});

function initLoginForm() {
    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value;
        const totpCode = document.getElementById('totpCode').value.trim();
        
        // 验证输入
        if (!username) {
            showFieldError('username', '请输入用户名');
            return;
        }
        
        if (!password) {
            showFieldError('password', '请输入密码');
            return;
        }
        
        if (!totpCode || totpCode.length !== 6 || !/^\d{6}$/.test(totpCode)) {
            showFieldError('totpCode', '请输入6位数字验证码');
            return;
        }
        
        await handleLogin(username, password, totpCode);
    });
    
    // 只允许输入数字到TOTP字段
    document.getElementById('totpCode').addEventListener('input', function(e) {
        this.value = this.value.replace(/\D/g, '');
    });
    
    // 清除错误状态
    document.getElementById('username').addEventListener('input', function() {
        clearFieldError('username');
    });
    
    document.getElementById('password').addEventListener('input', function() {
        clearFieldError('password');
    });
    
    document.getElementById('totpCode').addEventListener('input', function() {
        clearFieldError('totpCode');
    });
}

async function handleLogin(username, password, totpCode) {
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, totp_code: totpCode })
        });
        
        const data = await response.json();
        
        if (response.ok && data.access_token) {
            // 保存token
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('user', JSON.stringify(data.user));
            
            // 记住我
            const rememberMe = document.getElementById('rememberMe').checked;
            if (rememberMe) {
                localStorage.setItem('rememberMe', 'true');
                localStorage.setItem('savedUsername', username);
            } else {
                localStorage.removeItem('rememberMe');
                localStorage.removeItem('savedUsername');
            }
            
            showNotification('登录成功！', 'success');
            
            // 跳转到dashboard
            setTimeout(() => {
                window.location.href = 'dashboard.html';
            }, 500);
        } else {
            const errorMsg = data.detail || '登录失败';
            showNotification(errorMsg, 'error');
            
            // 清空TOTP输入
            document.getElementById('totpCode').value = '';
            document.getElementById('totpCode').focus();
        }
    } catch (error) {
        console.error('登录错误:', error);
        showNotification('网络错误，请检查服务器是否运行', 'error');
    } finally {
        showLoading(false);
    }
}

async function validateToken(token) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/me`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            // Token有效，直接跳转
            window.location.href = 'dashboard.html';
        } else {
            // Token无效，清除存储
            localStorage.removeItem('token');
            localStorage.removeItem('user');
        }
    } catch (error) {
        console.error('验证token失败:', error);
    }
}

function showForgotPassword() {
    showNotification('请联系管理员重置密码', 'info');
}

// ============ 工具函数 ============

function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
    input.setAttribute('type', type);
    
    const toggleBtn = input.parentElement.querySelector('.toggle-password i');
    if (toggleBtn) {
        toggleBtn.setAttribute('data-lucide', type === 'password' ? 'eye' : 'eye-off');
        lucide.createIcons();
    }
}

function showFieldError(fieldId, message) {
    const field = document.getElementById(fieldId);
    const formGroup = field.closest('.form-group');
    
    formGroup.classList.add('error');
    
    // 移除已有的错误提示
    const existingError = formGroup.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }
    
    // 添加错误提示
    const errorEl = document.createElement('span');
    errorEl.className = 'error-message';
    errorEl.textContent = message;
    formGroup.appendChild(errorEl);
}

function clearFieldError(fieldId) {
    const field = document.getElementById(fieldId);
    const formGroup = field.closest('.form-group');
    
    formGroup.classList.remove('error');
    
    const existingError = formGroup.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }
}

function showLoading(show) {
    if (show) {
        loadingOverlay.classList.add('show');
    } else {
        loadingOverlay.classList.remove('show');
    }
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    const iconName = type === 'success' ? 'check-circle' : 
                     type === 'error' ? 'alert-circle' : 'info';
    
    notification.innerHTML = `
        <i data-lucide="${iconName}"></i>
        <span>${message}</span>
    `;
    
    notificationContainer.appendChild(notification);
    lucide.createIcons();
    
    // 动画进入
    requestAnimationFrame(() => {
        notification.classList.add('show');
    });
    
    // 自动消失
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// 加载记住的用户名
document.addEventListener('DOMContentLoaded', function() {
    const savedUsername = localStorage.getItem('savedUsername');
    const rememberMe = localStorage.getItem('rememberMe');
    
    if (savedUsername && rememberMe === 'true') {
        document.getElementById('username').value = savedUsername;
        document.getElementById('rememberMe').checked = true;
    }
});
