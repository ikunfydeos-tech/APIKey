// 重构版注册页面脚本 - 强制TOTP

const API_BASE_URL = 'http://localhost:8000';

// 临时token存储
let tempToken = '';
let totpSecret = '';

// DOM元素
const step1 = document.getElementById('step1');
const step2 = document.getElementById('step2');
const step3 = document.getElementById('step3');
const loadingOverlay = document.getElementById('loadingOverlay');
const notificationContainer = document.getElementById('notificationContainer');

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化 Lucide 图标
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
    
    // 清除可能存在的旧登录状态
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    
    initStep1();
    initStep2();
    addPasswordStrengthIndicator();
});

// ============ 步骤1：基本信息 ============

function initStep1() {
    const form = document.getElementById('registerFormStep1');
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        const agreeTerms = document.getElementById('agreeTerms').checked;
        
        // 验证表单
        if (!validateStep1(username, password, confirmPassword, agreeTerms)) {
            return;
        }
        
        await submitStep1(username, password);
    });
    
    // 实时验证
    document.getElementById('username').addEventListener('blur', function() {
        validateUsername(this.value.trim());
    });
    
    document.getElementById('confirmPassword').addEventListener('input', function() {
        validatePasswordMatch();
    });
}

function validateStep1(username, password, confirmPassword, agreeTerms) {
    const isUsernameValid = validateUsername(username);
    const isPasswordValid = validatePassword(password);
    const isPasswordMatch = password === confirmPassword;
    
    if (!isPasswordMatch) {
        showFieldError('confirmPassword', '两次输入的密码不一致');
    }
    
    if (!agreeTerms) {
        showNotification('请先同意服务条款', 'error');
        return false;
    }
    
    return isUsernameValid && isPasswordValid && isPasswordMatch && agreeTerms;
}

function validateUsername(username) {
    clearFieldError('username');
    
    if (!username) {
        showFieldError('username', '请输入用户名');
        return false;
    }
    
    if (username.length < 3) {
        showFieldError('username', '用户名至少需要3个字符');
        return false;
    }
    
    if (username.length > 20) {
        showFieldError('username', '用户名不能超过20个字符');
        return false;
    }
    
    if (!/^[a-zA-Z0-9_-]+$/.test(username)) {
        showFieldError('username', '用户名只能包含字母、数字、下划线和连字符');
        return false;
    }
    
    return true;
}

function validatePassword(password) {
    clearFieldError('password');
    
    if (!password) {
        showFieldError('password', '请输入密码');
        return false;
    }
    
    if (password.length < 8) {
        showFieldError('password', '密码长度至少8位');
        return false;
    }
    
    // 检查是否包含数字、字母、特殊符号中的至少两项
    const hasLetter = /[a-zA-Z]/.test(password);
    const hasDigit = /[0-9]/.test(password);
    const hasSpecial = /[^a-zA-Z0-9]/.test(password);
    
    const typeCount = (hasLetter ? 1 : 0) + (hasDigit ? 1 : 0) + (hasSpecial ? 1 : 0);
    
    if (typeCount < 2) {
        showFieldError('password', '密码必须包含数字、字母、特殊符号中的至少两项');
        return false;
    }
    
    return true;
}

function validatePasswordMatch() {
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    
    clearFieldError('confirmPassword');
    
    if (!confirmPassword) {
        return false;
    }
    
    if (password !== confirmPassword) {
        showFieldError('confirmPassword', '两次输入的密码不一致');
        return false;
    }
    
    return true;
}

function addPasswordStrengthIndicator() {
    const passwordInput = document.getElementById('password');
    const strengthBar = document.getElementById('strengthBar');
    const passwordHint = document.getElementById('passwordHint');
    
    passwordInput.addEventListener('input', function() {
        const password = this.value;
        const result = calculatePasswordStrength(password);
        updatePasswordStrength(result);
        
        // 更新提示文字
        if (password.length === 0) {
            passwordHint.textContent = '密码需8位以上，包含数字、字母、特殊符号中的至少两项';
            passwordHint.style.color = '';
        } else if (!result.valid) {
            passwordHint.textContent = result.message;
            passwordHint.style.color = '#ef4444';
        } else {
            passwordHint.textContent = result.message;
            if (result.level === 'weak') {
                passwordHint.style.color = '#f59e0b';
            } else if (result.level === 'medium') {
                passwordHint.style.color = '#10b981';
            } else {
                passwordHint.style.color = '#059669';
            }
        }
    });
}

function calculatePasswordStrength(password) {
    const hasLower = /[a-z]/.test(password);
    const hasUpper = /[A-Z]/.test(password);
    const hasDigit = /[0-9]/.test(password);
    const hasSpecial = /[^a-zA-Z0-9]/.test(password);
    
    const hasLetter = hasLower || hasUpper;
    const typeCount = (hasLetter ? 1 : 0) + (hasDigit ? 1 : 0) + (hasSpecial ? 1 : 0);
    
    // 基本验证
    if (password.length < 8) {
        return { valid: false, level: 'invalid', strength: 0, message: '密码长度不足8位' };
    }
    
    if (typeCount < 2) {
        return { valid: false, level: 'invalid', strength: 20, message: '需包含数字、字母、特殊符号中的至少两项' };
    }
    
    // 计算强度
    let strength = 40; // 基础分：满足最低要求
    
    // 长度加分
    if (password.length >= 12) strength += 15;
    if (password.length >= 16) strength += 10;
    
    // 字符类型加分
    if (hasLower) strength += 5;
    if (hasUpper) strength += 10;
    if (hasDigit) strength += 5;
    if (hasSpecial) strength += 15;
    
    // 三种类型都包含
    if (typeCount === 3) strength += 10;
    
    // 确定等级
    let level, message;
    if (strength < 60) {
        level = 'weak';
        message = '密码强度：弱';
    } else if (strength < 80) {
        level = 'medium';
        message = '密码强度：中等';
    } else {
        level = 'strong';
        message = '密码强度：强';
    }
    
    return { valid: true, level, strength, message };
}

function updatePasswordStrength(result) {
    const strengthBar = document.getElementById('strengthBar');
    strengthBar.className = 'strength-bar';
    
    if (!result.valid) {
        strengthBar.classList.add('weak');
        strengthBar.style.width = result.strength + '%';
    } else if (result.level === 'weak') {
        strengthBar.classList.add('weak');
        strengthBar.style.width = result.strength + '%';
    } else if (result.level === 'medium') {
        strengthBar.classList.add('medium');
        strengthBar.style.width = result.strength + '%';
    } else {
        strengthBar.classList.add('strong');
        strengthBar.style.width = result.strength + '%';
    }
}

async function submitStep1(username, password) {
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/register/step1`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            tempToken = data.temp_token;
            totpSecret = data.totp_secret;
            
            // 显示二维码
            document.getElementById('totpQRCode').src = data.qr_code;
            document.getElementById('totpSecret').textContent = totpSecret;
            document.getElementById('qrLoading').style.display = 'none';
            
            goToStep(2);
        } else {
            const errorMsg = data.detail || '注册失败';
            if (errorMsg.includes('用户名')) {
                showFieldError('username', errorMsg);
            } else {
                showNotification(errorMsg, 'error');
            }
        }
    } catch (error) {
        console.error('注册错误:', error);
        showNotification('网络错误，请稍后重试', 'error');
    } finally {
        showLoading(false);
    }
}

// ============ 步骤2：TOTP验证 ============

function initStep2() {
    const form = document.getElementById('registerFormStep2');
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const totpCode = document.getElementById('totpCode').value.trim();
        
        if (!totpCode || totpCode.length !== 6 || !/^\d{6}$/.test(totpCode)) {
            showFieldError('totpCode', '请输入6位数字验证码');
            return;
        }
        
        await submitStep2(totpCode);
    });
    
    // 只允许输入数字
    document.getElementById('totpCode').addEventListener('input', function(e) {
        this.value = this.value.replace(/\D/g, '');
    });
}

async function submitStep2(totpCode) {
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/register/step2`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                temp_token: tempToken,
                totp_code: totpCode 
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.access_token) {
            // 注册成功，不保存token，让用户手动登录
            goToStep(3);
            startCountdown();
        } else {
            const errorMsg = data.detail || '验证失败';
            showFieldError('totpCode', errorMsg);
        }
    } catch (error) {
        console.error('验证错误:', error);
        showNotification('网络错误，请稍后重试', 'error');
    } finally {
        showLoading(false);
    }
}

function copySecret() {
    const secret = document.getElementById('totpSecret').textContent;
    navigator.clipboard.writeText(secret).then(() => {
        showNotification('密钥已复制到剪贴板', 'success');
    }).catch(() => {
        showNotification('复制失败，请手动复制', 'error');
    });
}

// ============ 步骤切换 ============

function goToStep(step) {
    // 隐藏所有步骤
    step1.classList.add('hidden');
    step2.classList.add('hidden');
    step3.classList.add('hidden');
    
    // 显示目标步骤
    document.getElementById(`step${step}`).classList.remove('hidden');
    
    // 更新步骤指示器
    updateStepIndicator(step);
}

function updateStepIndicator(currentStep) {
    const steps = document.querySelectorAll('.step');
    steps.forEach((step, index) => {
        const stepNum = index + 1;
        step.classList.remove('active', 'completed');
        
        if (stepNum === currentStep) {
            step.classList.add('active');
        } else if (stepNum < currentStep) {
            step.classList.add('completed');
        }
    });
}

function startCountdown() {
    let count = 3;
    const countdownEl = document.getElementById('countdown');
    
    const timer = setInterval(() => {
        count--;
        countdownEl.textContent = count;
        
        if (count <= 0) {
            clearInterval(timer);
            window.location.href = 'index.html';  // 跳转到登录页面
        }
    }, 1000);
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

// 键盘快捷键
document.addEventListener('keydown', function(e) {
    // ESC 返回上一步
    if (e.key === 'Escape' && !step2.classList.contains('hidden')) {
        goToStep(1);
    }
});
