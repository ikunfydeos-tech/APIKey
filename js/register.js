// 注册页面脚本

// API 基础地址（前后端端口分离：前端5500，后端8000）
const API_BASE_URL = 'http://localhost:8000';

// DOM 元素
const registerForm = document.getElementById('registerForm');
const usernameInput = document.getElementById('username');
const emailInput = document.getElementById('email');
const passwordInput = document.getElementById('password');
const confirmPasswordInput = document.getElementById('confirmPassword');
const agreeTermsCheckbox = document.getElementById('agreeTerms');
const loadingOverlay = document.getElementById('loadingOverlay');
const strengthBar = document.getElementById('strengthBar');

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    addFormValidation();
    addPasswordStrengthIndicator();
    addKeyboardShortcuts();
});

// 切换密码显示
function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
    input.setAttribute('type', type);
    
    const toggleBtn = input.parentElement.querySelector('.toggle-password');
    if (toggleBtn) {
        toggleBtn.innerHTML = '';
        const newIcon = document.createElement('i');
        newIcon.setAttribute('data-lucide', type === 'password' ? 'eye' : 'eye-off');
        toggleBtn.appendChild(newIcon);
        lucide.createIcons();
    }
}

// 添加密码强度指示器
function addPasswordStrengthIndicator() {
    passwordInput.addEventListener('input', function() {
        const strength = calculatePasswordStrength(this.value);
        updatePasswordStrength(strength);
    });
}

// 计算密码强度
function calculatePasswordStrength(password) {
    let strength = 0;
    
    if (password.length >= 6) strength += 20;
    if (password.length >= 8) strength += 10;
    if (password.length >= 12) strength += 10;
    if (/[a-z]/.test(password)) strength += 15;
    if (/[A-Z]/.test(password)) strength += 15;
    if (/[0-9]/.test(password)) strength += 15;
    if (/[^a-zA-Z0-9]/.test(password)) strength += 15;
    
    return strength;
}

// 更新密码强度显示
function updatePasswordStrength(strength) {
    strengthBar.className = 'strength-bar';
    
    if (strength < 30) {
        strengthBar.classList.add('weak');
    } else if (strength < 50) {
        strengthBar.classList.add('medium');
    } else if (strength < 70) {
        strengthBar.classList.add('strong');
    } else {
        strengthBar.classList.add('very-strong');
    }
}

// 添加表单验证
function addFormValidation() {
    // 用户名实时验证
    usernameInput.addEventListener('input', function() {
        validateUsername(this.value);
    });
    
    // 邮箱实时验证
    emailInput.addEventListener('input', function() {
        validateEmail(this.value);
    });
    
    // 确认密码实时验证
    confirmPasswordInput.addEventListener('input', function() {
        validatePasswordMatch();
    });
    
    // 密码变化时重新验证确认密码
    passwordInput.addEventListener('input', function() {
        if (confirmPasswordInput.value) {
            validatePasswordMatch();
        }
    });
    
    // 表单提交
    registerForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const username = usernameInput.value.trim();
        const email = emailInput.value.trim();
        const password = passwordInput.value;
        const confirmPassword = confirmPasswordInput.value;
        
        if (validateForm(username, email, password, confirmPassword)) {
            handleRegister(username, email, password);
        }
    });
}

// 验证用户名
function validateUsername(username) {
    const group = usernameInput.closest('.form-group');
    clearValidationState(group);
    
    if (!username) {
        showValidationError(group, '请输入用户名');
        return false;
    }
    
    if (username.length < 3) {
        showValidationError(group, '用户名至少需要3个字符');
        return false;
    }
    
    if (username.length > 20) {
        showValidationError(group, '用户名不能超过20个字符');
        return false;
    }
    
    if (!/^[a-zA-Z0-9_-]+$/.test(username)) {
        showValidationError(group, '用户名只能包含字母、数字、下划线和连字符');
        return false;
    }
    
    showValidationSuccess(group);
    return true;
}

// 验证邮箱
function validateEmail(email) {
    const group = emailInput.closest('.form-group');
    clearValidationState(group);
    
    if (!email) {
        showValidationError(group, '请输入邮箱');
        return false;
    }
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showValidationError(group, '请输入有效的邮箱地址');
        return false;
    }
    
    showValidationSuccess(group);
    return true;
}

// 验证密码匹配
function validatePasswordMatch() {
    const group = confirmPasswordInput.closest('.form-group');
    clearValidationState(group);
    
    const password = passwordInput.value;
    const confirmPassword = confirmPasswordInput.value;
    
    if (!confirmPassword) {
        return false;
    }
    
    if (password !== confirmPassword) {
        showValidationError(group, '两次输入的密码不一致');
        return false;
    }
    
    showValidationSuccess(group);
    return true;
}

// 清除验证状态
function clearValidationState(group) {
    group.classList.remove('error', 'success');
    const existingHint = group.querySelector('.error-hint');
    if (existingHint) existingHint.remove();
}

// 显示验证错误
function showValidationError(group, message) {
    group.classList.add('error');
    
    const hint = group.querySelector('.input-hint');
    if (hint) {
        hint.textContent = message;
        hint.style.color = '#ef4444';
    }
}

// 显示验证成功
function showValidationSuccess(group) {
    group.classList.add('success');
    
    const hint = group.querySelector('.input-hint');
    if (hint) {
        hint.style.color = 'var(--primary-color)';
    }
}

// 验证整个表单
function validateForm(username, email, password, confirmPassword) {
    const isUsernameValid = validateUsername(username);
    const isEmailValid = validateEmail(email);
    const isPasswordValid = password.length >= 6;
    const isPasswordMatch = password === confirmPassword;
    const isAgreed = agreeTermsCheckbox.checked;
    
    if (!isPasswordValid) {
        const group = passwordInput.closest('.form-group');
        showValidationError(group, '密码至少需要6个字符');
    }
    
    if (!isPasswordMatch) {
        validatePasswordMatch();
    }
    
    if (!isAgreed) {
        showNotification('请先同意服务条款', 'error');
    }
    
    return isUsernameValid && isEmailValid && isPasswordValid && isPasswordMatch && isAgreed;
}

// 处理注册逻辑
async function handleRegister(username, email, password) {
    try {
        showLoading(true);
        
        // 调用后端API进行注册
        const response = await fetch(`${API_BASE_URL}/api/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showNotification('注册成功！正在跳转到登录页面...', 'success');
            
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 1500);
        } else {
            const errorMsg = data.detail || '注册失败，用户名或邮箱已被使用';
            showNotification(errorMsg, 'error');
        }
    } catch (error) {
        console.error('注册错误:', error);
        showNotification('注册失败，请检查网络连接', 'error');
    } finally {
        showLoading(false);
    }
}

// 显示加载动画
function showLoading(show) {
    loadingOverlay.style.display = show ? 'flex' : 'none';
}

// 显示通知
function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    const iconName = type === 'success' ? 'check-circle' : 'alert-circle';
    
    notification.innerHTML = `
        <div class="notification-content">
            <i data-lucide="${iconName}"></i>
            <span>${message}</span>
        </div>
    `;
    
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? 'rgba(0, 184, 148, 0.95)' : 'rgba(239, 68, 68, 0.95)'};
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
    
    document.body.appendChild(notification);
    lucide.createIcons();
    
    const icon = notification.querySelector('i svg');
    if (icon) {
        icon.style.width = '20px';
        icon.style.height = '20px';
        icon.style.stroke = 'white';
    }
    
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// 添加键盘快捷键
function addKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + Enter 快速提交
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            registerForm.dispatchEvent(new Event('submit'));
        }
        
        // Escape 清除表单
        if (e.key === 'Escape') {
            registerForm.reset();
            document.querySelectorAll('.form-group').forEach(group => {
                clearValidationState(group);
            });
            strengthBar.className = 'strength-bar';
        }
    });
}

// 添加动画样式
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);