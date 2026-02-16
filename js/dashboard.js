// Dashboard 页面脚本

// API 基础地址（前后端端口分离：前端5500，后端8000）
const API_BASE_URL = 'http://localhost:8000';

// 数据存储
let apiKeys = [];
let providers = {};
let allModels = [];

// 刷新状态锁
let isRefreshing = false;

// 搜索防抖定时器
let searchTimeout = null;

// 服务商图标映射（Lucide 图标名称）
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

// 模型分类映射
const categoryMap = {
    'chat': { name: '对话', icon: 'message-circle', color: '#3b82f6' },
    'code': { name: '代码', icon: 'code', color: '#10b981' },
    'long_context': { name: '长文本', icon: 'file-text', color: '#8b5cf6' },
    'economy': { name: '经济', icon: 'coins', color: '#f59e0b' },
    'vision': { name: '多模态', icon: 'eye', color: '#ec4899' }
};

// 获取 Lucide 图标名称
function getLucideIcon(iconName) {
    return providerIconMap[iconName] || 'key';
}

// DOM 元素
const keysTableBody = document.getElementById('keysTableBody');
const emptyState = document.getElementById('emptyState');
const addModal = document.getElementById('addModal');
const deleteModal = document.getElementById('deleteModal');
const keyForm = document.getElementById('keyForm');
const providerSelect = document.getElementById('provider');
const modelSelect = document.getElementById('model');

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

// 页面初始化
document.addEventListener('DOMContentLoaded', async function() {
    const isLoggedIn = await checkLoginStatus();
    if (isLoggedIn) {
        displayUsername();
        await loadProviders();
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
        // 验证token有效性
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

// 显示用户名
function displayUsername() {
    const userStr = localStorage.getItem('user');
    if (userStr) {
        const user = JSON.parse(userStr);
        document.getElementById('usernameDisplay').textContent = user.username || '用户';
        
        // 如果是管理员，显示管理后台入口
        if (user.role === 'admin') {
            const adminNav = document.getElementById('navAdmin');
            if (adminNav) {
                adminNav.style.display = 'flex';
            }
        }
    }
}

// 加载服务商列表
async function loadProviders() {
    try {
        const [providersRes, modelsRes] = await Promise.all([
            fetch(`${API_BASE_URL}/api/keys/providers`, {
                headers: getAuthHeaders()
            }),
            fetch(`${API_BASE_URL}/api/keys/models`, {
                headers: getAuthHeaders()
            })
        ]);
        
        // 处理认证错误
        if (providersRes.status === 401 || modelsRes.status === 401) {
            handleAuthError();
            return;
        }
        
        // 处理服务商响应
        if (providersRes.ok) {
            const data = await providersRes.json();
            providers = {};
            data.forEach(p => {
                providers[p.id] = { name: p.display_name, icon: getLucideIcon(p.icon) };
            });
            renderProviderSelect(data);
        } else {
            const errorData = await providersRes.json().catch(() => ({}));
            console.error('加载服务商失败:', providersRes.status, errorData);
            showToast(`加载服务商失败: ${errorData.detail || '服务器错误'}`, 'error');
            return;
        }
        
        // 处理模型响应
        if (modelsRes.ok) {
            allModels = await modelsRes.json();
        } else {
            console.error('加载模型列表失败:', modelsRes.status);
            // 模型加载失败不影响主要功能，只记录日志
            allModels = [];
        }
        
        loadApiKeys();
    } catch (error) {
        console.error('加载服务商失败:', error);
        if (error.message && error.message.includes('Failed to fetch')) {
            showToast('无法连接到服务器，请检查后端服务是否运行', 'error');
        } else {
            showToast('加载服务商失败: ' + error.message, 'error');
        }
    }
}

// 渲染服务商选择器
function renderProviderSelect(providerList) {
    // 分离预设服务商和自定义服务商
    const presetProviders = providerList.filter(p => !p.is_custom);
    const customProviders = providerList.filter(p => p.is_custom);
    
    let html = '<option value="">请选择服务商</option>';
    
    // 预设服务商
    presetProviders.forEach(p => {
        html += `<option value="${p.id}" data-is-custom="false">${p.display_name}</option>`;
    });
    
    // 自定义服务商（如果有）
    if (customProviders.length > 0) {
        html += '<optgroup label="自定义服务商">';
        customProviders.forEach(p => {
            html += `<option value="${p.id}" data-is-custom="true">${p.display_name}</option>`;
        });
        html += '</optgroup>';
    }
    
    // 添加自定义服务商选项
    html += '<optgroup label="其他">';
    html += '<option value="__add_custom__" data-is-custom="true">➕ 添加自定义服务商...</option>';
    html += '</optgroup>';
    
    providerSelect.innerHTML = html;
}

// 服务商选择变化时加载对应模型
function onProviderChange() {
    const providerId = providerSelect.value;
    
    // 隐藏模型详情和测试结果
    document.getElementById('modelInfoRow').style.display = 'none';
    document.getElementById('testResultRow').style.display = 'none';
    
    // 检查是否选择了"添加自定义服务商"
    if (providerId === '__add_custom__') {
        openCustomProviderModal();
        // 重置选择
        providerSelect.value = '';
        return;
    }
    
    const parsedId = parseInt(providerId);
    
    // 获取当前选中的服务商信息
    const selectedOption = providerSelect.options[providerSelect.selectedIndex];
    const isCustom = selectedOption && selectedOption.dataset.isCustom === 'true';
    
    // 获取测试连接相关元素
    const testBtn = document.getElementById('testConnectionBtn');
    const testHint = document.getElementById('testHint');
    
    if (!providerId || parsedId <= 0) {
        modelSelect.innerHTML = '<option value="">不指定模型</option>';
        hideCustomModelInput();
        // 隐藏测试按钮和提示
        testBtn.style.display = 'none';
        testHint.style.display = 'none';
        return;
    }
    
    // 根据是否为自定义服务商显示/隐藏测试按钮
    if (isCustom) {
        testBtn.style.display = 'none';
        testHint.style.display = 'flex';
    } else {
        testBtn.style.display = 'flex';
        testHint.style.display = 'none';
    }
    
    // 检查是否为自定义服务商或"自定义"选项
    if (isCustom) {
        // 显示手动输入框
        showCustomModelInput();
        return;
    }
    
    const providerModels = allModels.filter(m => m.provider_id === parsedId);
    
    if (providerModels.length === 0) {
        // 没有预设模型，显示输入框
        showCustomModelInput();
        return;
    }
    
    // 有预设模型，显示下拉框+手动输入选项
    hideCustomModelInput();
    
    // 计算用户常用模型（根据已保存密钥中的使用频率）
    const modelUsageCount = {};
    apiKeys.forEach(key => {
        if (key.provider_id === providerId && key.model_id) {
            modelUsageCount[key.model_id] = (modelUsageCount[key.model_id] || 0) + 1;
        }
    });
    
    // 按使用频率排序模型
    providerModels.sort((a, b) => {
        const usageA = modelUsageCount[a.model_id] || 0;
        const usageB = modelUsageCount[b.model_id] || 0;
        // 使用频率高的排前面
        if (usageA !== usageB) {
            return usageB - usageA;
        }
        // 频率相同，默认模型排前面
        if (a.is_default && !b.is_default) return -1;
        if (!a.is_default && b.is_default) return 1;
        // 按原始排序
        return (a.sort_order || 0) - (b.sort_order || 0);
    });
    
    // 按分类分组
    const groupedModels = {};
    providerModels.forEach(m => {
        const cat = m.category || 'chat';
        if (!groupedModels[cat]) {
            groupedModels[cat] = [];
        }
        groupedModels[cat].push(m);
    });
    
    // 分类排序
    const categoryOrder = ['chat', 'code', 'vision', 'long_context', 'economy'];
    
    let optionsHtml = '<option value="">不指定模型</option>';
    
    // 添加常用模型分组（如果有）
    const frequentlyUsed = providerModels.filter(m => (modelUsageCount[m.model_id] || 0) > 0);
    if (frequentlyUsed.length > 0) {
        optionsHtml += '<optgroup label="📌 常用">';
        frequentlyUsed.forEach(m => {
            const contextInfo = m.context_window ? ` [${m.context_window}]` : '';
            const usageMark = modelUsageCount[m.model_id] > 0 ? ` (${modelUsageCount[m.model_id]}次)` : '';
            optionsHtml += `<option value="${m.model_id}">${m.model_name || m.model_id}${contextInfo}${usageMark}</option>`;
        });
        optionsHtml += '</optgroup>';
    }
    
    categoryOrder.forEach(cat => {
        if (groupedModels[cat] && groupedModels[cat].length > 0) {
            const catInfo = categoryMap[cat] || { name: cat, icon: 'circle', color: '#6b7280' };
            optionsHtml += `<optgroup label="${catInfo.name}">`;
            
            groupedModels[cat].forEach(m => {
                // 跳过已添加到常用分组的模型
                if ((modelUsageCount[m.model_id] || 0) > 0) return;
                
                const contextInfo = m.context_window ? ` [${m.context_window}]` : '';
                const defaultMark = m.is_default ? ' ⭐' : '';
                optionsHtml += `<option value="${m.model_id}">${m.model_name || m.model_id}${contextInfo}${defaultMark}</option>`;
            });
            
            optionsHtml += '</optgroup>';
        }
    });
    
    // 处理未分类的模型
    Object.keys(groupedModels).forEach(cat => {
        if (!categoryOrder.includes(cat)) {
            groupedModels[cat].forEach(m => {
                if ((modelUsageCount[m.model_id] || 0) > 0) return;
                const contextInfo = m.context_window ? ` [${m.context_window}]` : '';
                optionsHtml += `<option value="${m.model_id}">${m.model_name || m.model_id}${contextInfo}</option>`;
            });
        }
    });
    
    // 添加手动输入选项
    optionsHtml += '<optgroup label="其他"><option value="__custom__">✏️ 手动输入模型ID...</option></optgroup>';
    
    modelSelect.innerHTML = optionsHtml;
    
    // 自动选择使用频率最高的模型，或者默认模型
    const mostUsedModel = frequentlyUsed[0];
    const defaultModel = providerModels.find(m => m.is_default);
    
    if (mostUsedModel) {
        modelSelect.value = mostUsedModel.model_id;
    } else if (defaultModel) {
        modelSelect.value = defaultModel.model_id;
    }
    
    if (modelSelect.value) {
        onModelChange();
    }
}

// 模型选择变化时显示详情
function onModelChange() {
    const modelId = modelSelect.value;
    const modelInfoRow = document.getElementById('modelInfoRow');
    
    // 检查是否选择了"手动输入"选项
    if (modelId === '__custom__') {
        showCustomModelInput();
        modelInfoRow.style.display = 'none';
        return;
    }
    
    if (!modelId) {
        modelInfoRow.style.display = 'none';
        return;
    }
    
    const modelInfo = allModels.find(m => m.model_id === modelId);
    
    if (!modelInfo) {
        modelInfoRow.style.display = 'none';
        return;
    }
    
    // 更新模型详情显示
    document.getElementById('modelInfoName').textContent = modelInfo.model_name || modelInfo.model_id;
    document.getElementById('modelInfoId').textContent = modelInfo.model_id;
    document.getElementById('modelInfoContext').textContent = modelInfo.context_window || '未知';
    
    const categoryInfo = categoryMap[modelInfo.category] || { name: modelInfo.category || '未知' };
    document.getElementById('modelInfoCategory').textContent = categoryInfo.name;
    
    modelInfoRow.style.display = 'block';
    lucide.createIcons();
}

// 显示自定义模型输入框
function showCustomModelInput() {
    const modelInputGroup = document.getElementById('modelInputGroup');
    const modelSelectGroup = document.getElementById('model').closest('.form-group');
    
    if (modelInputGroup) {
        modelInputGroup.style.display = 'block';
    }
    if (modelSelectGroup) {
        modelSelectGroup.style.display = 'none';
    }
}

// 隐藏自定义模型输入框，显示下拉框
function hideCustomModelInput() {
    const modelInputGroup = document.getElementById('modelInputGroup');
    const modelSelectGroup = document.getElementById('model').closest('.form-group');
    
    if (modelInputGroup) {
        modelInputGroup.style.display = 'none';
    }
    if (modelSelectGroup) {
        modelSelectGroup.style.display = 'block';
    }
}

// 切换到下拉选择模型
function switchToModelSelect() {
    hideCustomModelInput();
    // 重新加载模型选项
    onProviderChange();
}

// 加载API密钥列表
async function loadApiKeys() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/keys`, {
            headers: getAuthHeaders()
        });
        
        if (response.ok) {
            apiKeys = await response.json();
            renderTable();
            updateStats();
        } else if (response.status === 401) {
            handleAuthError();
        } else {
            const errorData = await response.json().catch(() => ({}));
            console.error('加载密钥失败:', response.status, errorData);
            showToast(`加载密钥失败: ${errorData.detail || '服务器错误'}`, 'error');
        }
    } catch (error) {
        console.error('加载密钥失败:', error);
        if (error.message && error.message.includes('Failed to fetch')) {
            showToast('无法连接到服务器，请检查后端服务是否运行', 'error');
        } else {
            showToast('加载密钥失败: ' + error.message, 'error');
        }
    }
}

// 刷新数据
async function refreshData() {
    const refreshBtn = document.getElementById('refreshBtn');
    if (!refreshBtn) {
        console.error('找不到刷新按钮');
        showToast('页面初始化错误', 'error');
        return;
    }
    
    // 检查是否正在刷新
    if (isRefreshing) {
        showToast('正在刷新数据，请稍候', 'error');
        return;
    }
    
    // 获取 SVG 图标并添加旋转动画
    const svg = refreshBtn.querySelector('svg');
    if (svg) {
        svg.style.animation = 'spin 1s linear infinite';
    }
    
    isRefreshing = true;
    let success = true;
    
    try {
        // 设置超时
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000);
        
        // 并行请求
        const [providersRes, keysRes] = await Promise.all([
            fetch(`${API_BASE_URL}/api/keys/providers`, {
                headers: getAuthHeaders(),
                signal: controller.signal
            }),
            fetch(`${API_BASE_URL}/api/keys`, {
                headers: getAuthHeaders(),
                signal: controller.signal
            })
        ]);
        
        clearTimeout(timeoutId);
        
        // 处理服务商响应
        if (providersRes.ok) {
            const providersData = await providersRes.json();
            providers = {};
            providersData.forEach(p => {
                providers[p.id] = { name: p.display_name, icon: getLucideIcon(p.icon) };
            });
            renderProviderSelect(providersData);
        } else if (providersRes.status === 401) {
            handleAuthError();
            return;
        } else {
            success = false;
        }
        
        // 处理密钥响应
        if (keysRes.ok) {
            apiKeys = await keysRes.json();
            renderTable();
            updateStats();
        } else if (keysRes.status === 401) {
            handleAuthError();
            return;
        } else {
            success = false;
        }
        
        if (success) {
            showToast('数据已刷新', 'success');
        } else {
            showToast('部分数据加载失败', 'error');
        }
        
    } catch (error) {
        success = false;
        console.error('刷新失败:', error);
        
        if (error.name === 'AbortError') {
            showToast('请求超时，请检查网络连接', 'error');
        } else if (error.message && (error.message.includes('Failed to fetch') || error.message.includes('NetworkError'))) {
            showToast('网络连接失败，请检查网络', 'error');
        } else {
            showToast('刷新失败，请重试', 'error');
        }
    } finally {
        // 移除旋转动画
        const svg = refreshBtn.querySelector('svg');
        if (svg) {
            svg.style.animation = '';
        }
        // 释放刷新锁
        isRefreshing = false;
    }
}

// 处理认证错误
function handleAuthError() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = 'index.html';
}

// 初始化事件监听
function initEventListeners() {
    // 服务商选择变化
    providerSelect.addEventListener('change', function() {
        // customUrlGroup logic if needed
    });

    // 表单提交
    keyForm.addEventListener('submit', function(e) {
        e.preventDefault();
        saveKey();
    });
}

// 渲染表格
function renderTable(keysToRender = apiKeys) {
    if (keysToRender.length === 0) {
        keysTableBody.innerHTML = '';
        emptyState.style.display = 'block';
        return;
    }

    emptyState.style.display = 'none';
    keysTableBody.innerHTML = keysToRender.map(key => createTableRow(key)).join('');
    lucide.createIcons();
}

// 创建表格行
function createTableRow(key) {
    const provider = providers[key.provider_id] || { name: key.provider_name || '未知', icon: 'key' };
    const maskedKey = key.api_key_preview || '••••••••';
    const statusClass = key.status === 'active' ? 'active' : 'inactive';
    const statusText = key.status === 'active' ? '活跃' : '未激活';
    const statusIcon = key.status === 'active' ? 'check-circle' : 'pause-circle';
    
    // 获取模型信息
    let modelDisplay = '-';
    let modelId = null;
    let modelCategory = null;
    if (key.model_id) {
        const modelInfo = allModels.find(m => m.model_id === key.model_id);
        if (modelInfo) {
            modelDisplay = modelInfo.model_name || modelInfo.model_id;
            modelId = modelInfo.model_id;
            modelCategory = modelInfo.category;
        } else {
            modelDisplay = key.model_id;
            modelId = key.model_id;
        }
    }
    
    // 分类标签
    let categoryTag = '';
    if (modelCategory && categoryMap[modelCategory]) {
        const cat = categoryMap[modelCategory];
        categoryTag = `<span class="category-tag" style="background: ${cat.color}20; color: ${cat.color}; border: 1px solid ${cat.color}40;" title="${cat.name}">
            <i data-lucide="${cat.icon}" style="width: 12px; height: 12px;"></i>
        </span>`;
    }
    
    // 复制模型ID按钮
    let copyModelBtn = '';
    if (modelId) {
        copyModelBtn = `<button class="copy-btn copy-model-btn" onclick="copyModelId('${modelId}', this)" title="复制模型ID">
            <i data-lucide="copy"></i>
        </button>`;
    }
    
    return `
        <tr data-id="${key.id}">
            <td>
                <div class="provider-cell">
                    <div class="provider-icon">
                        <i data-lucide="${provider.icon}"></i>
                    </div>
                    <span class="provider-name">${provider.name}</span>
                </div>
            </td>
            <td>${key.key_name}</td>
            <td>
                <div class="model-cell">
                    ${categoryTag}
                    <code class="model-code">${modelDisplay}</code>
                    ${copyModelBtn}
                </div>
            </td>
            <td>
                <div class="key-cell">
                    <code>${maskedKey}</code>
                    <button class="copy-btn" onclick="copyKey(${key.id}, this)" title="复制密钥">
                        <i data-lucide="copy"></i>
                    </button>
                </div>
            </td>
            <td>
                <span class="status-badge ${statusClass}">
                    <i data-lucide="${statusIcon}"></i>
                    ${statusText}
                </span>
            </td>
            <td>${new Date(key.created_at).toLocaleDateString()}</td>
            <td>
                <div class="action-btns">
                    <button class="action-btn" onclick="editKey(${key.id})" title="编辑">
                        <i data-lucide="edit-2"></i>
                    </button>
                    <button class="action-btn" onclick="toggleKeyStatus(${key.id})" title="${key.status === 'active' ? '停用' : '启用'}">
                        <i data-lucide="${key.status === 'active' ? 'pause' : 'play'}"></i>
                    </button>
                    <button class="action-btn danger" onclick="openDeleteModal(${key.id})" title="删除">
                        <i data-lucide="trash-2"></i>
                    </button>
                </div>
            </td>
        </tr>
    `;
}

// 更新统计数据
function updateStats() {
    document.getElementById('totalKeys').textContent = apiKeys.length;
    document.getElementById('activeKeys').textContent = apiKeys.filter(k => k.status === 'active').length;
    document.getElementById('inactiveKeys').textContent = apiKeys.filter(k => k.status === 'inactive').length;
    document.getElementById('totalProviders').textContent = [...new Set(apiKeys.map(k => k.provider_id))].length;
}

// 搜索密钥
function searchKeys() {
    // 清除之前的定时器
    if (searchTimeout) {
        clearTimeout(searchTimeout);
    }
    
    // 延迟 300ms 执行搜索
    searchTimeout = setTimeout(() => {
        const query = document.getElementById('searchInput').value.trim().toLowerCase();
        if (!query) {
            renderTable(apiKeys);
            return;
        }
        
        const filtered = apiKeys.filter(k => 
            k.key_name.toLowerCase().includes(query) ||
            (k.provider_name && k.provider_name.toLowerCase().includes(query))
        );
        renderTable(filtered);
    }, 300);
}

// 按状态筛选
function filterByStatus() {
    const status = document.getElementById('statusFilter').value;
    let filtered;
    if (status === 'all') {
        filtered = apiKeys;
    } else {
        filtered = apiKeys.filter(k => k.status === status);
    }
    renderTable(filtered);
}

// 切换侧边栏
function toggleSidebar() {
    document.querySelector('.sidebar').classList.toggle('open');
}

// 打开添加弹窗
function openAddModal() {
    editingKeyId = null;
    document.getElementById('modalTitle').textContent = '添加API密钥';
    keyForm.reset();
    addModal.classList.add('active');
    lucide.createIcons();
}

// 关闭添加弹窗
function closeAddModal() {
    addModal.classList.remove('active');
    keyForm.reset();
    editingKeyId = null;
}

// 编辑密钥
async function editKey(id) {
    try {
        // 获取完整密钥（解密）
        const response = await fetch(`${API_BASE_URL}/api/keys/${id}`, {
            headers: getAuthHeaders()
        });
        
        if (response.ok) {
            const key = await response.json();
            
            editingKeyId = id;
            document.getElementById('modalTitle').textContent = '编辑API密钥';
            document.getElementById('keyId').value = id;
            document.getElementById('provider').value = key.provider_id || '';
            document.getElementById('keyName').value = key.key_name;
            document.getElementById('apiKey').value = key.api_key;
            document.getElementById('keyNote').value = key.notes || '';
            
            // 触发服务商变化以加载模型列表
            onProviderChange();
            
            // 如果有模型ID，等待模型列表加载后设置模型选择
            if (key.model_id) {
                setTimeout(() => {
                    // 检查模型是否在预设列表中
                    const modelInList = allModels.find(m => m.model_id === key.model_id);
                    
                    if (modelInList) {
                        // 模型在列表中，设置下拉框值
                        document.getElementById('model').value = key.model_id;
                        onModelChange();
                    } else {
                        // 模型不在列表中，显示输入框并填入模型ID
                        showCustomModelInput();
                        const customInput = document.getElementById('customModelInput');
                        if (customInput) {
                            customInput.value = key.model_id;
                        }
                    }
                }, 100);
            }
            
            addModal.classList.add('active');
            lucide.createIcons();
        }
    } catch (error) {
        console.error('获取密钥失败:', error);
        showToast('获取密钥失败', 'error');
    }
}

// 保存密钥
async function saveKey() {
    const providerValue = document.getElementById('provider').value.trim();
    const providerId = parseInt(providerValue);
    const modelId = getModelValue();  // 使用统一的模型值获取函数
    const name = document.getElementById('keyName').value.trim();
    const key = document.getElementById('apiKey').value.trim();
    const note = document.getElementById('keyNote').value.trim();

    if (!providerValue || !name || !key) {
        showToast('请填写必填字段', 'error');
        return;
    }

    try {
        let response;
        
        if (editingKeyId) {
            // 更新密钥
            response = await fetch(`${API_BASE_URL}/api/keys/${editingKeyId}`, {
                method: 'PUT',
                headers: getAuthHeaders(),
                body: JSON.stringify({
                    key_name: name,
                    api_key: key,
                    model_id: modelId,
                    notes: note
                })
            });
        } else {
            // 添加新密钥
            response = await fetch(`${API_BASE_URL}/api/keys`, {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({
                    provider_id: providerId,
                    key_name: name,
                    api_key: key,
                    model_id: modelId,
                    notes: note
                })
            });
        }

        if (response.ok) {
            showToast(editingKeyId ? '密钥更新成功' : '密钥添加成功', 'success');
            closeAddModal();
            loadApiKeys();
        } else {
            const error = await response.json();
            showToast(error.detail || '操作失败', 'error');
        }
    } catch (error) {
        console.error('保存密钥失败:', error);
        showToast('保存密钥失败', 'error');
    }
}

// 切换密钥状态
async function toggleKeyStatus(id) {
    const key = apiKeys.find(k => k.id === id);
    if (!key) return;
    
    const newStatus = key.status === 'active' ? 'inactive' : 'active';
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/keys/${id}`, {
            method: 'PUT',
            headers: getAuthHeaders(),
            body: JSON.stringify({ status: newStatus })
        });
        
        if (response.ok) {
            showToast(`密钥已${newStatus === 'active' ? '启用' : '停用'}`, 'success');
            loadApiKeys();
        }
    } catch (error) {
        console.error('更新状态失败:', error);
        showToast('更新状态失败', 'error');
    }
}

// 打开删除确认弹窗
function openDeleteModal(id) {
    deletingKeyId = id;
    deleteModal.classList.add('active');
}

// 关闭删除确认弹窗
function closeDeleteModal() {
    deleteModal.classList.remove('active');
    deletingKeyId = null;
}

// 确认删除
async function confirmDelete() {
    if (!deletingKeyId) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/keys/${deletingKeyId}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });
        
        if (response.ok) {
            showToast('密钥已删除', 'success');
            closeDeleteModal();
            loadApiKeys();
        }
    } catch (error) {
        console.error('删除密钥失败:', error);
        showToast('删除密钥失败', 'error');
    }
}

// 复制到剪贴板（兼容 file:// 协议）
function copyToClipboard(text) {
    // 优先使用现代 API
    if (navigator.clipboard && window.isSecureContext) {
        return navigator.clipboard.writeText(text);
    }
    
    // 降级方案：使用 execCommand
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.left = '-9999px';
    textarea.style.top = '-9999px';
    document.body.appendChild(textarea);
    textarea.focus();
    textarea.select();
    
    try {
        const success = document.execCommand('copy');
        document.body.removeChild(textarea);
        return Promise.resolve();
    } catch (err) {
        document.body.removeChild(textarea);
        return Promise.reject(err);
    }
}

// 复制密钥
async function copyKey(id, button) {
    try {
        // 获取完整密钥
        const response = await fetch(`${API_BASE_URL}/api/keys/${id}`, {
            headers: getAuthHeaders()
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('获取密钥成功:', data.key_name);
            
            try {
                await copyToClipboard(data.api_key);
                
                // Lucide 会将 <i> 替换为 <svg>，所以需要查找 svg
                const icon = button.querySelector('svg');
                if (icon) {
                    icon.setAttribute('data-lucide', 'check');
                    icon.outerHTML = icon.outerHTML.replace('lucide-copy', 'lucide-check');
                    lucide.createIcons();
                }
                
                showToast('密钥已复制到剪贴板', 'success');
                
                setTimeout(() => {
                    const newIcon = button.querySelector('svg');
                    if (newIcon) {
                        newIcon.outerHTML = newIcon.outerHTML.replace('lucide-check', 'lucide-copy');
                        lucide.createIcons();
                    }
                }, 2000);
            } catch (copyErr) {
                console.error('剪贴板写入失败:', copyErr);
                showToast('复制失败，请手动复制密钥', 'error');
            }
        } else {
            const errorData = await response.json();
            console.error('获取密钥失败:', errorData);
            showToast('获取密钥失败: ' + (errorData.detail || '未知错误'), 'error');
        }
    } catch (err) {
        console.error('请求失败:', err);
        showToast('网络请求失败，请检查连接', 'error');
    }
}

// 复制模型ID
async function copyModelId(modelId, button) {
    if (!modelId) {
        showToast('没有模型ID可复制', 'error');
        return;
    }
    
    try {
        await copyToClipboard(modelId);
        
        // 更新图标为勾选状态
        const icon = button.querySelector('svg');
        if (icon) {
            icon.outerHTML = icon.outerHTML.replace('lucide-copy', 'lucide-check');
            lucide.createIcons();
        }
        
        showToast(`模型ID "${modelId}" 已复制`, 'success');
        
        // 恢复图标
        setTimeout(() => {
            const newIcon = button.querySelector('svg');
            if (newIcon) {
                newIcon.outerHTML = newIcon.outerHTML.replace('lucide-check', 'lucide-copy');
                lucide.createIcons();
            }
        }, 2000);
    } catch (err) {
        console.error('复制失败:', err);
        showToast('复制失败', 'error');
    }
}

// 切换密码显示
function toggleKeyPassword() {
    const input = document.getElementById('apiKey');
    const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
    input.setAttribute('type', type);
    
    const toggleBtn = document.querySelector('.toggle-password');
    if (toggleBtn) {
        toggleBtn.innerHTML = '';
        const newIcon = document.createElement('i');
        newIcon.setAttribute('data-lucide', type === 'password' ? 'eye' : 'eye-off');
        toggleBtn.appendChild(newIcon);
        lucide.createIcons();
    }
}

// 退出登录
function handleLogout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = 'index.html';
}

// 显示 Toast 通知
function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const iconName = type === 'success' ? 'check-circle' : 'alert-circle';
    
    toast.innerHTML = `
        <i data-lucide="${iconName}"></i>
        <span>${message}</span>
    `;
    
    container.appendChild(toast);
    lucide.createIcons();
    
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease-out reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ============ 自定义服务商功能 ============

// 打开自定义服务商弹窗
function openCustomProviderModal() {
    const modal = document.getElementById('customProviderModal');
    if (modal) {
        modal.classList.add('active');
        lucide.createIcons();
    }
}

// 关闭自定义服务商弹窗
function closeCustomProviderModal() {
    const modal = document.getElementById('customProviderModal');
    if (modal) {
        modal.classList.remove('active');
        // 重置表单
        document.getElementById('customProviderForm').reset();
    }
}

// 保存自定义服务商
async function saveCustomProvider() {
    const displayName = document.getElementById('customProviderName').value.trim();
    const baseUrl = document.getElementById('customProviderUrl').value.trim();
    const description = document.getElementById('customProviderDesc').value.trim();
    
    if (!displayName || !baseUrl) {
        showToast('请填写服务商名称和API地址', 'error');
        return;
    }
    
    // 验证 URL 格式
    try {
        new URL(baseUrl);
    } catch {
        showToast('请输入有效的API地址', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/keys/providers`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                display_name: displayName,
                base_url: baseUrl,
                description: description || null
            })
        });
        
        if (response.ok) {
            const newProvider = await response.json();
            showToast('服务商添加成功', 'success');
            closeCustomProviderModal();
            
            // 重新加载服务商列表
            await loadProviders();
            
            // 自动选中新添加的服务商
            setTimeout(() => {
                providerSelect.value = newProvider.id;
                onProviderChange();
            }, 100);
        } else {
            const error = await response.json();
            showToast(error.detail || '添加失败', 'error');
        }
    } catch (error) {
        console.error('添加服务商失败:', error);
        showToast('添加服务商失败', 'error');
    }
}

// 获取模型值（下拉框或输入框）
function getModelValue() {
    const modelInputGroup = document.getElementById('modelInputGroup');
    
    // 检查是否显示自定义输入框
    if (modelInputGroup && modelInputGroup.style.display !== 'none') {
        const customInput = document.getElementById('customModelInput');
        return customInput ? customInput.value.trim() : null;
    }
    
    // 检查下拉框是否选择了手动输入
    const modelId = modelSelect.value;
    if (modelId === '__custom__') {
        const customInput = document.getElementById('customModelInput');
        return customInput ? customInput.value.trim() : null;
    }
    
    return modelId || null;
}

// ============ 服务商配置弹窗功能 ============

// 打开服务商配置弹窗
function openProviderConfigModal() {
    renderProviderConfigList();
    document.getElementById('providerConfigModal').classList.add('active');
    lucide.createIcons();
    
    // 更新导航状态
    updateNavActive('navProviderConfig');
}

// 关闭服务商配置弹窗
function closeProviderConfigModal() {
    document.getElementById('providerConfigModal').classList.remove('active');
    
    // 恢复导航状态
    updateNavActive('navKeyManage');
}

// 更新导航激活状态
function updateNavActive(activeId) {
    document.querySelectorAll('.sidebar-nav .nav-item').forEach(item => {
        item.classList.remove('active');
    });
    const activeNav = document.getElementById(activeId);
    if (activeNav) {
        activeNav.classList.add('active');
    }
}

// 切换到密钥管理
function switchToKeyManage() {
    document.getElementById('keyManagePage').style.display = 'block';
    document.getElementById('usagePage').style.display = 'none';
    document.getElementById('currentPageName').textContent = '密钥管理';
    closeProviderConfigModal();
    // 在 closeProviderConfigModal 之后调用，确保导航状态正确
    updateNavActive('navKeyManage');
}

// 显示功能开发中提示
function showComingSoon(featureName) {
    showToast(`${featureName}功能开发中，敬请期待`, 'error');
}

// 渲染服务商配置列表
async function renderProviderConfigList() {
    const listContainer = document.getElementById('providerConfigList');
    
    if (Object.keys(providers).length === 0) {
        await loadProviders();
    }
    
    // 获取每个服务商的密钥数量
    const providerKeyCount = {};
    apiKeys.forEach(key => {
        if (key.provider_id) {
            providerKeyCount[key.provider_id] = (providerKeyCount[key.provider_id] || 0) + 1;
        }
    });
    
    // 获取每个服务商的模型数量
    const providerModelCount = {};
    allModels.forEach(model => {
        providerModelCount[model.provider_id] = (providerModelCount[model.provider_id] || 0) + 1;
    });
    
    let html = '';
    
    Object.entries(providers).forEach(([id, provider]) => {
        const keyCount = providerKeyCount[id] || 0;
        const modelCount = providerModelCount[id] || 0;
        
        html += `
            <div class="provider-config-item">
                <div class="provider-config-icon">
                    <i data-lucide="${provider.icon}"></i>
                </div>
                <div class="provider-config-info">
                    <div class="provider-config-name">${provider.name}</div>
                    <div class="provider-config-stats">
                        <span><i data-lucide="key"></i> ${keyCount} 个密钥</span>
                        <span><i data-lucide="cpu"></i> ${modelCount} 个模型</span>
                    </div>
                </div>
                <div class="provider-config-actions">
                    <button class="action-btn" onclick="addKeyForProvider(${id})" title="添加密钥">
                        <i data-lucide="plus"></i>
                    </button>
                </div>
            </div>
        `;
    });
    
    listContainer.innerHTML = html;
    document.getElementById('providerCount').textContent = Object.keys(providers).length;
    lucide.createIcons();
}

// 为指定服务商添加密钥
function addKeyForProvider(providerId) {
    closeProviderConfigModal();
    openAddModal();
    setTimeout(() => {
        providerSelect.value = providerId;
        onProviderChange();
    }, 100);
}

// 测试 API 连接
async function testApiConnection() {
    const providerId = providerSelect.value;
    const apiKey = document.getElementById('apiKey').value.trim();
    
    if (!providerId) {
        showToast('请先选择服务商', 'error');
        return;
    }
    
    if (!apiKey) {
        showToast('请输入API密钥', 'error');
        return;
    }
    
    const testBtn = document.getElementById('testConnectionBtn');
    const testResultRow = document.getElementById('testResultRow');
    const testResultCard = document.getElementById('testResultCard');
    const testResultIcon = document.getElementById('testResultIcon');
    const testResultTitle = document.getElementById('testResultTitle');
    const testResultMessage = document.getElementById('testResultMessage');
    
    // 显示测试中状态
    testBtn.disabled = true;
    testBtn.classList.add('testing');
    testResultRow.style.display = 'block';
    testResultCard.className = 'test-result-card testing';
    testResultIcon.innerHTML = '<i data-lucide="loader-2"></i>';
    testResultTitle.textContent = '正在测试连接...';
    testResultMessage.textContent = '请稍候';
    lucide.createIcons();
    
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/api/keys/test`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                provider_id: parseInt(providerId),
                api_key: apiKey
            })
        });
        
        const result = await response.json();
        
        // 显示结果
        if (result.success) {
            testResultCard.className = 'test-result-card success';
            testResultIcon.innerHTML = '<i data-lucide="check-circle"></i>';
            testResultTitle.textContent = '连接成功';
            testResultMessage.textContent = result.message;
        } else {
            testResultCard.className = 'test-result-card error';
            testResultIcon.innerHTML = '<i data-lucide="x-circle"></i>';
            testResultTitle.textContent = '连接失败';
            testResultMessage.textContent = result.message;
        }
        
        lucide.createIcons();
        
    } catch (error) {
        console.error('测试连接错误:', error);
        testResultCard.className = 'test-result-card error';
        testResultIcon.innerHTML = '<i data-lucide="x-circle"></i>';
        testResultTitle.textContent = '测试失败';
        testResultMessage.textContent = '网络错误，请稍后重试';
        lucide.createIcons();
    } finally {
        testBtn.disabled = false;
        testBtn.classList.remove('testing');
    }
}

// ===== 使用统计页面 =====

let requestsChart = null;
let providerChart = null;
let currentTimeRange = 7;

// 切换到使用统计页面
function switchToUsage() {
    document.getElementById('keyManagePage').style.display = 'none';
    document.getElementById('usagePage').style.display = 'block';
    document.getElementById('currentPageName').textContent = '使用统计';
    closeProviderConfigModal();
    // 在 closeProviderConfigModal 之后调用，否则会被覆盖
    updateNavActive('navUsage');
    loadUsageData();
}

// 设置时间范围
function setTimeRange(days) {
    currentTimeRange = days;
    // 更新按钮状态
    document.querySelectorAll('.time-btn').forEach(btn => {
        btn.classList.remove('active');
        if (parseInt(btn.dataset.range) === days) {
            btn.classList.add('active');
        }
    });
    loadUsageData();
}

// 加载使用统计数据（模拟数据）
function loadUsageData() {
    // 模拟数据
    const mockData = generateMockUsageData(currentTimeRange);
    
    // 更新统计卡片
    document.getElementById('totalRequests').textContent = formatNumber(mockData.totalRequests);
    document.getElementById('totalTokens').textContent = formatNumber(mockData.totalTokens);
    document.getElementById('activeKeysUsage').textContent = mockData.activeKeys;
    document.getElementById('avgResponseTime').textContent = mockData.avgResponseTime + 'ms';
    
    // 渲染图表
    renderRequestsChart(mockData.trendData);
    renderProviderChart(mockData.providerData);
    
    // 渲染使用排行表格
    renderUsageTable(mockData.keyUsageData);
}

// 生成模拟数据
function generateMockUsageData(days) {
    const trendData = [];
    const today = new Date();
    
    for (let i = days - 1; i >= 0; i--) {
        const date = new Date(today);
        date.setDate(date.getDate() - i);
        trendData.push({
            date: `${date.getMonth() + 1}/${date.getDate()}`,
            requests: Math.floor(Math.random() * 500) + 100,
            tokens: Math.floor(Math.random() * 50000) + 10000
        });
    }
    
    const providerData = [
        { name: 'OpenAI', value: 45, color: '#10b981' },
        { name: 'Anthropic', value: 25, color: '#8b5cf6' },
        { name: 'DeepSeek', value: 15, color: '#3b82f6' },
        { name: '智谱AI', value: 10, color: '#f59e0b' },
        { name: '其他', value: 5, color: '#6b7280' }
    ];
    
    const keyUsageData = apiKeys.slice(0, 5).map((key, index) => ({
        name: key.key_name,
        provider: key.provider_name,
        requests: Math.floor(Math.random() * 1000) + 50,
        inputTokens: Math.floor(Math.random() * 50000) + 5000,
        outputTokens: Math.floor(Math.random() * 20000) + 2000,
        lastUsed: key.last_used_at || '刚刚'
    }));
    
    // 如果没有真实密钥数据，添加模拟数据
    if (keyUsageData.length === 0) {
        keyUsageData.push(
            { name: '生产环境密钥', provider: 'OpenAI', requests: 1250, inputTokens: 125000, outputTokens: 45000, lastUsed: '2分钟前' },
            { name: '测试密钥', provider: 'Anthropic', requests: 856, inputTokens: 85000, outputTokens: 32000, lastUsed: '1小时前' },
            { name: '开发环境', provider: 'DeepSeek', requests: 423, inputTokens: 42000, outputTokens: 15000, lastUsed: '3小时前' },
            { name: '备用密钥', provider: '智谱AI', requests: 234, inputTokens: 23000, outputTokens: 8000, lastUsed: '昨天' },
            { name: '实验密钥', provider: 'OpenAI', requests: 156, inputTokens: 15000, outputTokens: 5000, lastUsed: '2天前' }
        );
    }
    
    return {
        totalRequests: trendData.reduce((sum, d) => sum + d.requests, 0),
        totalTokens: trendData.reduce((sum, d) => sum + d.tokens, 0),
        activeKeys: apiKeys.filter(k => k.status === 'active').length || 5,
        avgResponseTime: Math.floor(Math.random() * 200) + 100,
        trendData,
        providerData,
        keyUsageData
    };
}

// 格式化数字
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

// 渲染请求趋势图
function renderRequestsChart(data) {
    const ctx = document.getElementById('requestsChart').getContext('2d');
    
    if (requestsChart) {
        requestsChart.destroy();
    }
    
    requestsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d => d.date),
            datasets: [{
                label: '请求数',
                data: data.map(d => d.requests),
                borderColor: '#00d4aa',
                backgroundColor: 'rgba(0, 212, 170, 0.1)',
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    },
                    ticks: {
                        color: '#94a3b8'
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    },
                    ticks: {
                        color: '#94a3b8'
                    }
                }
            }
        }
    });
}

// 渲染服务商分布图
function renderProviderChart(data) {
    const ctx = document.getElementById('providerChart').getContext('2d');
    
    if (providerChart) {
        providerChart.destroy();
    }
    
    providerChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.map(d => d.name),
            datasets: [{
                data: data.map(d => d.value),
                backgroundColor: data.map(d => d.color),
                borderWidth: 0,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#e2e8f0',
                        padding: 15,
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                }
            },
            cutout: '60%'
        }
    });
}

// 渲染使用排行表格
function renderUsageTable(data) {
    const tbody = document.getElementById('usageTableBody');
    
    if (data.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" style="text-align: center; padding: 2rem; color: var(--text-muted);">
                    暂无使用数据
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = data.map(item => `
        <tr>
            <td>
                <span style="color: var(--text-primary); font-weight: 500;">${item.name}</span>
            </td>
            <td>${item.provider}</td>
            <td>
                <span style="color: #10b981; font-weight: 600;">${formatNumber(item.requests)}</span>
            </td>
            <td>
                <span class="token-input">${formatNumber(item.inputTokens)}</span>
                <span style="color: var(--text-muted);">/</span>
                <span class="token-output">${formatNumber(item.outputTokens)}</span>
            </td>
            <td style="color: var(--text-muted);">${item.lastUsed}</td>
        </tr>
    `).join('');
}
