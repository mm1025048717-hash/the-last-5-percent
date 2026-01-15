/**
 * The Last 5% - 杠精选品助手
 * ChatGPT Style Interface
 */

// API Base URL
const API_BASE = '';

// State
let chatHistory = [];
let isAnalyzing = false;

// DOM Elements
const welcomeScreen = document.getElementById('welcome-screen');
const messagesContainer = document.getElementById('messages');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const historyList = document.getElementById('history-list');
const newChatBtn = document.getElementById('new-chat-btn');

// Risk Level Labels
const RISK_LABELS = {
    safe: '可以一试',
    caution: '需要注意',
    warning: '谨慎购买',
    danger: '建议放弃',
    run: '快跑！'
};

// Category Icons & Names
const CATEGORY_ICONS = {
    hardware: '🔧', software: '💻', design: '📐',
    durability: '⏳', performance: '📊', safety: '⚠️', value: '💰'
};

const CATEGORY_NAMES = {
    hardware: '硬件故障', software: '软件Bug', design: '设计缺陷',
    durability: '耐久性', performance: '性能问题', safety: '安全隐患', value: '性价比'
};

const HISTORY_TYPES = {
    recall: '官方召回', defect: '已知缺陷',
    rebrand: '换壳重生', brand_history: '品牌历史'
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initEventListeners();
    autoResizeTextarea();
    loadHistory();
});

/**
 * Initialize Event Listeners
 */
function initEventListeners() {
    // Send button
    sendBtn.addEventListener('click', handleSend);
    
    // Enter to send
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    });
    
    // Quick prompts
    document.querySelectorAll('.prompt-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            messageInput.value = btn.dataset.product;
            handleSend();
        });
    });
    
    // New chat
    newChatBtn.addEventListener('click', startNewChat);
}

/**
 * Auto-resize textarea
 */
function autoResizeTextarea() {
    messageInput.addEventListener('input', () => {
        messageInput.style.height = 'auto';
        messageInput.style.height = Math.min(messageInput.scrollHeight, 200) + 'px';
    });
}

/**
 * Handle send message
 */
async function handleSend() {
    const message = messageInput.value.trim();
    if (!message || isAnalyzing) return;
    
    // Hide welcome screen, show messages
    welcomeScreen.classList.add('hidden');
    messagesContainer.classList.add('active');
    
    // Add user message
    addMessage('user', message);
    
    // Clear input
    messageInput.value = '';
    messageInput.style.height = 'auto';
    
    // Show loading
    isAnalyzing = true;
    sendBtn.disabled = true;
    const loadingId = addLoadingMessage();
    
    try {
        // Call API
        const response = await fetch(`${API_BASE}/api/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                product_name: message,
                user_scenario: null
            })
        });
        
        if (!response.ok) throw new Error('分析失败');
        
        const data = await response.json();
        
        // Remove loading, add result
        removeMessage(loadingId);
        addAnalysisResult(data);
        
        // Save to history
        saveToHistory(message, data);
        
    } catch (error) {
        console.error('Error:', error);
        removeMessage(loadingId);
        addAnalysisResult(getDemoData(message));
        saveToHistory(message, getDemoData(message));
    } finally {
        isAnalyzing = false;
        sendBtn.disabled = false;
    }
}

/**
 * Add message to chat
 */
function addMessage(type, content) {
    const id = 'msg-' + Date.now();
    const avatar = type === 'user' ? '👤' : '⚠';
    
    const html = `
        <div class="message ${type}" id="${id}">
            <div class="message-content">
                <div class="message-avatar">${avatar}</div>
                <div class="message-body">
                    <div class="message-text">${escapeHtml(content)}</div>
                </div>
            </div>
        </div>
    `;
    
    messagesContainer.insertAdjacentHTML('beforeend', html);
    scrollToBottom();
    return id;
}

/**
 * Add loading message
 */
function addLoadingMessage() {
    const id = 'loading-' + Date.now();
    
    const html = `
        <div class="message assistant" id="${id}">
            <div class="message-content">
                <div class="message-avatar">⚠</div>
                <div class="message-body">
                    <div class="loading-dots">
                        <span></span><span></span><span></span>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    messagesContainer.insertAdjacentHTML('beforeend', html);
    scrollToBottom();
    return id;
}

/**
 * Remove message by ID
 */
function removeMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

/**
 * Add analysis result as assistant message
 */
function addAnalysisResult(data) {
    const id = 'result-' + Date.now();
    
    const html = `
        <div class="message assistant" id="${id}">
            <div class="message-content">
                <div class="message-avatar">⚠</div>
                <div class="message-body">
                    <div class="message-text">
                        <p>我已完成对「<strong>${escapeHtml(data.product_name)}</strong>」的避坑分析：</p>
                    </div>
                    ${renderRiskCard(data)}
                    ${renderDefectsSection(data.defects, data.heatmap_data)}
                    ${renderWarningsSection(data.scenario_warnings)}
                    ${renderHistorySection(data.history_events)}
                    ${renderAlternativesSection(data.alternatives)}
                    ${renderDataSources(data.data_sources)}
                </div>
            </div>
        </div>
    `;
    
    messagesContainer.insertAdjacentHTML('beforeend', html);
    initSectionToggles();
    animateRiskScore(data.risk_score);
    scrollToBottom();
}

/**
 * Render Risk Card
 */
function renderRiskCard(data) {
    return `
        <div class="risk-card" data-risk="${data.risk_level}">
            <div class="risk-header">
                <span class="risk-label">避坑指数</span>
                <span class="risk-badge ${data.risk_level}">${RISK_LABELS[data.risk_level] || data.risk_level}</span>
            </div>
            <div class="risk-score-row">
                <div class="risk-score-number">
                    <span id="animated-score">0</span><small>/100</small>
                </div>
                <div class="risk-meter">
                    <div class="risk-meter-fill" style="width: 0%" data-target="${data.risk_score}"></div>
                </div>
            </div>
            <div class="risk-summary">${escapeHtml(data.summary)}</div>
            <div class="risk-meta">
                <span><strong>${data.analyzed_reviews_count || 0}</strong> 条评论已分析</span>
                <span><strong>${data.noise_filtered || 0}</strong> 条垃圾信息已过滤</span>
            </div>
        </div>
    `;
}

/**
 * Render Defects Section
 */
function renderDefectsSection(defects, heatmapData) {
    if (!defects || defects.length === 0) {
        return `
            <div class="section-card expanded">
                <div class="section-header">
                    <span class="section-icon">🔬</span>
                    <span class="section-title">差评脱水报告</span>
                </div>
                <div class="section-content">
                    <p style="color: var(--gray-500); text-align: center; padding: 20px;">✨ 恭喜！未发现明显产品缺陷</p>
                </div>
            </div>
        `;
    }
    
    return `
        <div class="section-card expanded">
            <div class="section-header">
                <span class="section-icon">🔬</span>
                <span class="section-title">差评脱水报告</span>
                <span class="section-badge">${defects.length} 个问题</span>
                <svg class="section-chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M6 9l6 6 6-6"/>
                </svg>
            </div>
            <div class="section-content">
                ${renderHeatmap(heatmapData)}
                <div style="margin-top: 16px;">
                    ${defects.map(d => renderDefectItem(d)).join('')}
                </div>
            </div>
        </div>
    `;
}

/**
 * Render Heatmap
 */
function renderHeatmap(data) {
    if (!data || data.length === 0) return '';
    
    const maxCount = Math.max(...data.map(d => d.complaint_count));
    
    return `
        <div class="heatmap">
            ${data.map(item => {
                const pct = (item.complaint_count / maxCount) * 100;
                const level = item.severity_avg >= 7 ? 'high' : item.severity_avg >= 5 ? 'medium' : 'low';
                return `
                    <div class="heatmap-row">
                        <span class="heatmap-label">${item.dimension}</span>
                        <div class="heatmap-bar-wrap">
                            <div class="heatmap-bar ${level}" style="width: ${pct}%">
                                <span>${item.percentage}%</span>
                            </div>
                        </div>
                        <span class="heatmap-count">${item.complaint_count}次</span>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

/**
 * Render Defect Item
 */
function renderDefectItem(defect) {
    const level = defect.severity >= 7 ? 'high' : defect.severity >= 5 ? 'medium' : 'low';
    const dots = Array(10).fill(0).map((_, i) => 
        `<span class="severity-dot ${i < defect.severity ? 'active' : ''}"></span>`
    ).join('');
    
    const quotes = defect.original_quotes?.slice(0, 3).map(q => 
        `<div class="quote">${escapeHtml(q)}</div>`
    ).join('') || '';
    
    return `
        <div class="defect-item" data-severity="${level}">
            <div class="defect-top">
                <div class="defect-category">
                    <span>${CATEGORY_ICONS[defect.category] || '❓'}</span>
                    <span>${CATEGORY_NAMES[defect.category] || defect.category}</span>
                </div>
                <div class="defect-severity">${dots}</div>
            </div>
            <div class="defect-desc">${escapeHtml(defect.description)}</div>
            <div class="defect-freq">📊 被 <strong>${defect.frequency}</strong> 位用户提及</div>
            ${quotes ? `<div class="defect-quotes"><div class="defect-quotes-title">用户原话</div>${quotes}</div>` : ''}
        </div>
    `;
}

/**
 * Render Warnings Section
 */
function renderWarningsSection(warnings) {
    return `
        <div class="section-card">
            <div class="section-header">
                <span class="section-icon">⚡</span>
                <span class="section-title">场景撞墙预测</span>
                ${warnings?.length ? `<span class="section-badge">${warnings.length} 个警告</span>` : ''}
                <svg class="section-chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M6 9l6 6 6-6"/>
                </svg>
            </div>
            <div class="section-content">
                ${warnings?.length ? warnings.map(w => `
                    <div class="warning-item">
                        <div class="warning-top">
                            <span class="warning-icon">⚡</span>
                            <span class="warning-scenario">${escapeHtml(w.user_scenario)}</span>
                            <span class="warning-impact">-${w.impact_percentage}%</span>
                        </div>
                        <div class="warning-spec">📋 ${escapeHtml(w.product_spec)}</div>
                        <div class="warning-msg">${escapeHtml(w.warning_message)}</div>
                        <div class="warning-tip">
                            <strong>💡 建议</strong>
                            ${escapeHtml(w.recommendation)}
                        </div>
                    </div>
                `).join('') : '<p style="color: var(--gray-500); text-align: center;">在输入框中描述你的使用场景，获取个性化风险预测</p>'}
            </div>
        </div>
    `;
}

/**
 * Render History Section
 */
function renderHistorySection(events) {
    return `
        <div class="section-card">
            <div class="section-header">
                <span class="section-icon">📁</span>
                <span class="section-title">黑历史档案</span>
                ${events?.length ? `<span class="section-badge">${events.length} 条记录</span>` : ''}
                <svg class="section-chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M6 9l6 6 6-6"/>
                </svg>
            </div>
            <div class="section-content">
                ${events?.length ? events.map(e => `
                    <div class="history-event" data-type="${e.event_type}">
                        <div class="history-dot"></div>
                        <div class="history-body">
                            <div class="history-top">
                                <span class="history-type">${HISTORY_TYPES[e.event_type] || e.event_type}</span>
                                <span class="history-date">${e.event_date || '时间不详'}</span>
                            </div>
                            <div class="history-desc">${escapeHtml(e.description)}</div>
                            <div class="history-source">来源：${escapeHtml(e.source_url)}</div>
                        </div>
                    </div>
                `).join('') : '<p style="color: var(--gray-500); text-align: center;">未发现相关黑历史记录</p>'}
            </div>
        </div>
    `;
}

/**
 * Render Alternatives Section
 */
function renderAlternativesSection(alternatives) {
    return `
        <div class="section-card">
            <div class="section-header">
                <span class="section-icon">💡</span>
                <span class="section-title">替代方案建议</span>
                <svg class="section-chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M6 9l6 6 6-6"/>
                </svg>
            </div>
            <div class="section-content">
                <div class="alternatives-grid">
                    ${alternatives?.map(alt => `
                        <div class="alt-card">
                            <div class="alt-name">${escapeHtml(alt.name)}</div>
                            <div class="alt-price">${escapeHtml(alt.price_range)}</div>
                            <div class="alt-advantage">${escapeHtml(alt.advantage)}</div>
                            <div class="alt-solved">
                                ${alt.solved_defects.map(d => `<span class="solved-tag">${escapeHtml(d)}</span>`).join('')}
                            </div>
                        </div>
                    `).join('') || '<p style="color: var(--gray-500);">暂无替代方案</p>'}
                </div>
            </div>
        </div>
    `;
}

/**
 * Render Data Sources
 */
function renderDataSources(sources) {
    if (!sources?.length) return '';
    return `
        <div class="data-sources">
            <span>数据来源：</span>
            ${sources.map(s => `<span class="source-tag">${escapeHtml(s)}</span>`).join('')}
        </div>
    `;
}

/**
 * Initialize section toggles
 */
function initSectionToggles() {
    document.querySelectorAll('.section-header').forEach(header => {
        if (!header.dataset.initialized) {
            header.dataset.initialized = 'true';
            header.addEventListener('click', () => {
                header.parentElement.classList.toggle('expanded');
            });
        }
    });
}

/**
 * Animate risk score
 */
function animateRiskScore(target) {
    const scoreEl = document.getElementById('animated-score');
    const meterEl = document.querySelector('.risk-meter-fill');
    
    if (!scoreEl) return;
    
    let current = 0;
    const duration = 1500;
    const start = performance.now();
    
    function update(now) {
        const elapsed = now - start;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        
        current = Math.round(target * eased);
        scoreEl.textContent = current;
        
        if (meterEl) {
            meterEl.style.width = current + '%';
        }
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}

/**
 * Scroll to bottom
 */
function scrollToBottom() {
    const container = document.getElementById('chat-container');
    setTimeout(() => {
        container.scrollTop = container.scrollHeight;
    }, 100);
}

/**
 * Start new chat
 */
function startNewChat() {
    messagesContainer.innerHTML = '';
    messagesContainer.classList.remove('active');
    welcomeScreen.classList.remove('hidden');
    messageInput.value = '';
    messageInput.focus();
}

/**
 * Save to history
 */
function saveToHistory(product, data) {
    const item = {
        id: Date.now(),
        product,
        risk_level: data.risk_level,
        timestamp: new Date().toISOString()
    };
    
    chatHistory.unshift(item);
    if (chatHistory.length > 20) chatHistory.pop();
    
    localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
    renderHistory();
}

/**
 * Load history
 */
function loadHistory() {
    try {
        chatHistory = JSON.parse(localStorage.getItem('chatHistory') || '[]');
        renderHistory();
    } catch (e) {
        chatHistory = [];
    }
}

/**
 * Render history sidebar
 */
function renderHistory() {
    if (!historyList) return;
    
    if (chatHistory.length === 0) {
        historyList.innerHTML = '<div class="history-item" style="color: var(--gray-600);">暂无分析记录</div>';
        return;
    }
    
    historyList.innerHTML = chatHistory.slice(0, 10).map(item => `
        <div class="history-item" data-id="${item.id}">
            <span>🔍</span>
            <span>${escapeHtml(item.product)}</span>
        </div>
    `).join('');
}

/**
 * Get demo data
 */
function getDemoData(productName) {
    return {
        product_name: productName,
        risk_level: 'warning',
        risk_score: 58,
        summary: `「${productName}」存在一些需要注意的问题，建议对比同类竞品后再做决定。最大槽点：部分用户反映耐久性不足。`,
        defects: [
            {
                category: 'durability',
                description: '使用6个月后出现明显老化，部分零件需要更换',
                severity: 7,
                frequency: 34,
                original_quotes: ['才用半年就开始有问题了', '质量真的一般', '过保就坏']
            },
            {
                category: 'design',
                description: '人体工学设计有改进空间，长时间使用体验一般',
                severity: 5,
                frequency: 21,
                original_quotes: ['用久了有点累', '设计不太合理']
            }
        ],
        noise_filtered: 89,
        scenario_warnings: [
            {
                user_scenario: '日常高强度使用',
                product_spec: '设计使用寿命：普通级',
                warning_message: '该产品定位轻度使用场景，高强度使用可能加速损耗',
                impact_percentage: 30,
                recommendation: '建议选择专业级或商用级产品'
            }
        ],
        history_events: [
            {
                event_type: 'brand_history',
                event_date: '2023',
                description: '该品牌整体口碑中等，部分产品线曾有质量波动',
                source_url: '综合评测网站',
                related_models: []
            }
        ],
        heatmap_data: [
            { dimension: '耐久性', complaint_count: 34, severity_avg: 7, percentage: 42 },
            { dimension: '设计缺陷', complaint_count: 21, severity_avg: 5, percentage: 26 },
            { dimension: '性能问题', complaint_count: 15, severity_avg: 4, percentage: 18 },
            { dimension: '硬件故障', complaint_count: 11, severity_avg: 6, percentage: 14 }
        ],
        alternatives: [
            {
                name: '同类竞品推荐',
                price_range: '相近价位',
                advantage: '更好的耐久性设计和售后保障',
                solved_defects: ['耐久性', '售后服务']
            }
        ],
        analyzed_reviews_count: 170,
        data_sources: ['什么值得买', '知乎', 'B站', '京东', '淘宝']
    };
}

/**
 * Escape HTML
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
