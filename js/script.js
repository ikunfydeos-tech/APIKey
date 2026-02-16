// 全局变量
const loginForm = document.getElementById('loginForm');
const usernameInput = document.getElementById('username');
const passwordInput = document.getElementById('password');
const rememberMeCheckbox = document.getElementById('rememberMe');
const loadingOverlay = document.getElementById('loadingOverlay');

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 检查是否记住登录状态
    loadRememberedCredentials();
    
    // 添加表单验证
    addFormValidation();
    
    // 添加键盘事件监听
    addKeyboardShortcuts();
});

// 加载记住的登录凭据
function loadRememberedCredentials() {
    const savedUsername = localStorage.getItem('rememberedUsername');
    const savedPassword = localStorage.getItem('rememberedPassword');
    const rememberMe = localStorage.getItem('rememberMe') === 'true';
    
    if (rememberMe && savedUsername) {
        usernameInput.value = savedUsername;
        passwordInput.value = savedPassword || '';
        rememberMeCheckbox.checked = true;
    }
}

// 保存登录凭据
function saveCredentials() {
    if (rememberMeCheckbox.checked) {
        localStorage.setItem('rememberedUsername', usernameInput.value);
        localStorage.setItem('rememberedPassword', passwordInput.value);
        localStorage.setItem('rememberMe', 'true');
    } else {
        localStorage.removeItem('rememberedUsername');
        localStorage.removeItem('rememberedPassword');
        localStorage.setItem('rememberMe', 'false');
    }
}

// 删除保存的登录凭据
function clearSavedCredentials() {
    localStorage.removeItem('rememberedUsername');
    localStorage.removeItem('rememberedPassword');
    localStorage.setItem('rememberMe', 'false');
    rememberMeCheckbox.checked = false;
}

// 切换密码显示
function togglePassword() {
    const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
    passwordInput.setAttribute('type', type);
    
    // 获取切换按钮，更新其内容
    const toggleBtn = document.querySelector('.toggle-password');
    if (toggleBtn) {
        // 清空按钮内容并创建新的图标元素
        toggleBtn.innerHTML = '';
        const newIcon = document.createElement('i');
        newIcon.setAttribute('data-lucide', type === 'password' ? 'eye' : 'eye-off');
        toggleBtn.appendChild(newIcon);
        // 重新渲染 Lucide 图标
        lucide.createIcons();
    }
}

// 添加表单验证
function addFormValidation() {
    // 实时验证用户名
    usernameInput.addEventListener('blur', function() {
        validateUsername(this.value);
    });
    
    // 实时验证密码
    passwordInput.addEventListener('blur', function() {
        validatePassword(this.value);
    });
    
    // 表单提交验证
    loginForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const username = usernameInput.value.trim();
        const password = passwordInput.value;
        
        if (validateForm(username, password)) {
            handleLogin(username, password);
        }
    });
}

// 验证用户名
function validateUsername(username) {
    const usernameGroup = usernameInput.parentElement.parentElement;
    const errorIcon = usernameGroup.querySelector('.error-icon');
    
    // 清除之前的错误状态
    usernameGroup.classList.remove('error');
    if (errorIcon) errorIcon.remove();
    
    if (!username) {
        showError(usernameGroup, '请输入用户名');
        return false;
    }
    
    if (username.length < 3) {
        showError(usernameGroup, '用户名至少需要3个字符');
        return false;
    }
    
    if (username.length > 20) {
        showError(usernameGroup, '用户名不能超过20个字符');
        return false;
    }
    
    if (!/^[a-zA-Z0-9_-]+$/.test(username)) {
        showError(usernameGroup, '用户名只能包含字母、数字、下划线和连字符');
        return false;
    }
    
    return true;
}

// 验证密码
function validatePassword(password) {
    const passwordGroup = passwordInput.parentElement.parentElement;
    const errorIcon = passwordGroup.querySelector('.error-icon');
    
    // 清除之前的错误状态
    passwordGroup.classList.remove('error');
    if (errorIcon) errorIcon.remove();
    
    if (!password) {
        showError(passwordGroup, '请输入密码');
        return false;
    }
    
    if (password.length < 6) {
        showError(passwordGroup, '密码至少需要6个字符');
        return false;
    }
    
    if (password.length > 50) {
        showError(passwordGroup, '密码不能超过50个字符');
        return false;
    }
    
    return true;
}

// 显示错误信息
function showError(inputGroup, message) {
    inputGroup.classList.add('error');
}

// 验证整个表单
function validateForm(username, password) {
    const isUsernameValid = validateUsername(username);
    const isPasswordValid = validatePassword(password);
    
    return isUsernameValid && isPasswordValid;
}

// 处理登录逻辑
async function handleLogin(username, password) {
    try {
        // 显示加载动画
        showLoading(true);
        
        // 调用后端API验证登录
        const isValidLogin = await validateCredentials(username, password);
        
        if (isValidLogin) {
            // 保存登录凭据（记住用户名密码功能）
            saveCredentials();
            
            // 显示成功提示
            showSuccessMessage('登录成功！正在跳转...');
            
            // 跳转到主页
            setTimeout(() => {
                window.location.href = 'dashboard.html';
            }, 1500);
        } else {
            // 显示错误信息
            showErrorMessage('用户名或密码错误');
            shakeForm();
        }
    } catch (error) {
        console.error('登录错误:', error);
        showErrorMessage('登录失败，请稍后重试');
    } finally {
        showLoading(false);
    }
}

// API 基础地址（前后端端口分离：前端5500，后端8000）
const API_BASE_URL = 'http://localhost:8000';

// 验证凭据（调用后端API）
async function validateCredentials(username, password) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        
        if (response.ok) {
            const data = await response.json();
            // 保存 JWT token
            localStorage.setItem('token', data.access_token);
            // 保存用户信息
            localStorage.setItem('user', JSON.stringify(data.user));
            return true;
        } else {
            const error = await response.json();
            console.error('登录失败:', error);
            return false;
        }
    } catch (error) {
        console.error('API调用错误:', error);
        return false;
    }
}

// 显示加载动画
function showLoading(show) {
    if (show) {
        loadingOverlay.style.display = 'flex';
    } else {
        loadingOverlay.style.display = 'none';
    }
}

// 显示成功消息
function showSuccessMessage(message) {
    // 创建成功消息元素
    const successMessage = document.createElement('div');
    successMessage.className = 'notification success';
    successMessage.innerHTML = `
        <div class="notification-content">
            <i data-lucide="check-circle"></i>
            <span>${message}</span>
        </div>
    `;
    
    successMessage.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: rgba(16, 185, 129, 0.95);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: var(--border-radius);
        box-shadow: var(--shadow-lg);
        z-index: 9998;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        animation: slideInRight 0.3s ease-out;
    `;
    
    document.body.appendChild(successMessage);
    
    // 渲染 Lucide 图标
    lucide.createIcons();
    
    // 设置图标样式
    const icon = successMessage.querySelector('i svg');
    if (icon) {
        icon.style.width = '20px';
        icon.style.height = '20px';
        icon.style.stroke = 'white';
    }
    
    // 3秒后自动移除
    setTimeout(() => {
        successMessage.style.animation = 'slideOutRight 0.3s ease-out';
        setTimeout(() => {
            if (successMessage.parentNode) {
                successMessage.parentNode.removeChild(successMessage);
            }
        }, 300);
    }, 3000);
}

// 显示错误消息
function showErrorMessage(message) {
    // 创建错误消息元素
    const errorMessage = document.createElement('div');
    errorMessage.className = 'notification error';
    errorMessage.innerHTML = `
        <div class="notification-content">
            <i data-lucide="alert-circle"></i>
            <span>${message}</span>
        </div>
    `;
    
    errorMessage.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: rgba(239, 68, 68, 0.95);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: var(--border-radius);
        box-shadow: var(--shadow-lg);
        z-index: 9998;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        animation: slideInRight 0.3s ease-out;
    `;
    
    document.body.appendChild(errorMessage);
    
    // 渲染 Lucide 图标
    lucide.createIcons();
    
    // 设置图标样式
    const icon = errorMessage.querySelector('i svg');
    if (icon) {
        icon.style.width = '20px';
        icon.style.height = '20px';
        icon.style.stroke = 'white';
    }
    
    // 3秒后自动移除
    setTimeout(() => {
        errorMessage.style.animation = 'slideOutRight 0.3s ease-out';
        setTimeout(() => {
            if (errorMessage.parentNode) {
                errorMessage.parentNode.removeChild(errorMessage);
            }
        }, 300);
    }, 3000);
}

// 表单抖动效果
function shakeForm() {
    loginForm.style.animation = 'shake 0.5s ease-in-out';
    setTimeout(() => {
        loginForm.style.animation = '';
    }, 500);
}

// 添加键盘快捷键
function addKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + Enter 快速登录
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            loginForm.dispatchEvent(new Event('submit'));
        }
        
        // Escape 清除表单
        if (e.key === 'Escape') {
            loginForm.reset();
            clearSavedCredentials();
        }
    });
}

// 添加CSS动画
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        10%, 30%, 50%, 70%, 90% { transform: translateX(-10px); }
        20%, 40%, 60%, 80% { transform: translateX(10px); }
    }
    
    .notification {
        animation: slideInRight 0.3s ease-out;
    }
    
    .notification.error {
        background: rgba(239, 68, 68, 0.95);
    }
    
    .notification.success {
        background: rgba(16, 185, 129, 0.95);
    }
    
    .notification-content {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .error-icon {
        animation: pulse 1s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
`;
document.head.appendChild(style);

// 添加密码强度指示器（可选功能）
function addPasswordStrengthIndicator() {
    const passwordGroup = passwordInput.parentElement.parentElement;
    
    const strengthIndicator = document.createElement('div');
    strengthIndicator.id = 'passwordStrength';
    strengthIndicator.style.cssText = `
        height: 3px;
        background: var(--gray-200);
        border-radius: 2px;
        margin-top: 0.5rem;
        overflow: hidden;
        transition: var(--transition);
    `;
    
    const strengthBar = document.createElement('div');
    strengthBar.id = 'strengthBar';
    strengthBar.style.cssText = `
        height: 100%;
        width: 0%;
        background: var(--danger-color);
        transition: var(--transition);
        border-radius: 2px;
    `;
    
    strengthIndicator.appendChild(strengthBar);
    passwordGroup.appendChild(strengthIndicator);
    
    // 监听密码输入
    passwordInput.addEventListener('input', function() {
        const strength = calculatePasswordStrength(this.value);
        updatePasswordStrength(strength, strengthBar);
    });
}

// 计算密码强度
function calculatePasswordStrength(password) {
    let strength = 0;
    
    if (password.length >= 6) strength += 25;
    if (password.length >= 8) strength += 15;
    if (/[a-z]/.test(password)) strength += 15;
    if (/[A-Z]/.test(password)) strength += 15;
    if (/[0-9]/.test(password)) strength += 15;
    if (/[^a-zA-Z0-9]/.test(password)) strength += 15;
    
    return strength;
}

// 更新密码强度显示
function updatePasswordStrength(strength, bar) {
    const colors = ['#ef4444', '#f59e0b', '#3b82f6', '#10b981'];
    const labels = ['弱', '中', '强', '极强'];
    
    if (strength < 40) {
        bar.style.background = colors[0];
        bar.style.width = '25%';
    } else if (strength < 60) {
        bar.style.background = colors[1];
        bar.style.width = '50%';
    } else if (strength < 80) {
        bar.style.background = colors[2];
        bar.style.width = '75%';
    } else {
        bar.style.background = colors[3];
        bar.style.width = '100%';
    }
}

// 初始化密码强度指示器
document.addEventListener('DOMContentLoaded', function() {
    if (passwordInput) {
        addPasswordStrengthIndicator();
    }
});

// 添加复制功能到dashboard页面（如果存在）
if (window.location.pathname.includes('dashboard.html')) {
    document.addEventListener('DOMContentLoaded', function() {
        // 添加复制功能
        const copyButtons = document.querySelectorAll('.copy-btn');
        copyButtons.forEach(button => {
            button.addEventListener('click', function() {
                const text = this.getAttribute('data-text');
                copyToClipboard(text, this);
            });
        });
    });
}

// 复制到剪贴板
function copyToClipboard(text, button) {
    navigator.clipboard.writeText(text).then(() => {
        const originalHTML = button.innerHTML;
        button.innerHTML = '<i class="fas fa-check"></i> 已复制';
        button.style.background = 'var(--success-color)';
        
        setTimeout(() => {
            button.innerHTML = originalHTML;
            button.style.background = '';
        }, 2000);
    }).catch(err => {
        console.error('复制失败:', err);
        button.innerHTML = '<i class="fas fa-times"></i> 复制失败';
        button.style.background = 'var(--danger-color)';
        
        setTimeout(() => {
            button.innerHTML = originalHTML;
            button.style.background = '';
        }, 2000);
    });
}