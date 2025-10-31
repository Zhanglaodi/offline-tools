class LinksHub {
    constructor() {
        this.tools = this.loadInitialData();
        this.filteredTools = [...this.tools];
        this.currentView = 'grid';
        this.activeFilters = new Set();
        this.currentEditingId = null;
        this.isDarkTheme = localStorage.getItem('linksHub_theme') === 'dark';

        this.init();
    }

    init() {
        this.applyTheme();
        this.bindEvents();
        this.render();
        this.updateStats();
        this.renderTagFilters();
        this.initKeyboardShortcuts();
    }

    loadInitialData() {
        // 检查localStorage中是否有数据
        const savedData = localStorage.getItem('linksHub_tools');
        if (savedData) {
            try {
                return JSON.parse(savedData);
            } catch (e) {
                console.warn('Failed to parse saved data, using default data');
            }
        }

        // 使用你提供的初始数据
        const initialData = [
            { id: this.generateId(), title: 'DBC 编写工具', url: './tools/dbc_editor/index.html', desc: '本地页面：修复跨行注释的 DBC 可视化。', tags: ['CAN', 'DBC', '前端'], kind: 'LOCAL', online: true, favorited: false },
            { id: this.generateId(), title: '进制转换工具', url: './tools/base_converter/index.html', desc: '进制之间互转', tags: ['进制', '工具'], kind: 'LOCAL', online: true, favorited: true },
            { id: this.generateId(), title: '波特率计算工具', url: './tools/baud_rate/index.html', desc: '波特率计算', tags: ['波特率', '调试'], kind: 'LOCAL', online: true, favorited: false },
            { id: this.generateId(), title: '创芯曲线工具', url: './tools/创芯科技/index.html', desc: '创新科技曲线工具,只支持csv文件', tags: ['曲线', '创芯', '工具'], kind: 'LOCAL', online: true, favorited: false },
            { id: this.generateId(), title: '周立功曲线工具', url: './tools/周立功/index.html', desc: '支持解析ASC文件', tags: ['曲线', '周立功', '工具'], kind: 'LOCAL', online: true, favorited: false },
            { id: this.generateId(), title: '串口工具-网页', url: './tools/serial/index.html', desc: '串口工具-仅供娱乐', tags: ['串口', '工具'], kind: 'LOCAL', online: true, favorited: false },
            { id: this.generateId(), title: '塞弗转向-计算轮距', url: './tools/塞弗转向-计算轮距/index.html', desc: '塞弗转向-计算轮距', tags: ['汽车', '工具'], kind: 'LOCAL', online: true, favorited: false },
            { id: this.generateId(), title: 'CRC-校验', url: './tools/CRC-校验/index.html', desc: '支持自定义多项式，支持多种CRC校验', tags: ['工具', 'CRC校验'], kind: 'LOCAL', online: true, favorited: false },
            { id: this.generateId(), title: 'BCC-校验', url: './tools/BCC校验/index.html', desc: '支持BCC校验', tags: ['工具', 'BCC校验'], kind: 'LOCAL', online: true, favorited: false },
            { id: this.generateId(), title: 'STM32 文档 (F4 HAL)', url: 'https://www.st.com/en/embedded-software/stm32cube-mcu-packages.html', desc: 'F4 HAL 参考与例程入口。', tags: ['STM32', 'HAL', '文档'], kind: 'WEB', online: true, favorited: false },
            { id: this.generateId(), title: 'ASC曲线工具(独立运行版)', url: 'https://pan.baidu.com/s/5iUl1EJqsuVKNUqp-m0dtJg', desc: 'asc文件曲线工具', tags: ['zlg', '曲线', '汽车'], kind: 'WEB', online: true, favorited: false }
        ];

        // 添加创建时间和更新时间
        initialData.forEach(tool => {
            tool.createdAt = new Date().toISOString();
            tool.updatedAt = new Date().toISOString();
        });

        // 保存到localStorage
        this.saveData(initialData);
        return initialData;
    }

    bindEvents() {
        // 搜索功能
        const searchInput = document.getElementById('search-input');
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.filterTools(e.target.value);
            }, 300);
        });

        // 添加工具按钮
        document.getElementById('add-tool').addEventListener('click', () => {
            this.showModal();
        });

        // 模态框事件
        document.getElementById('close-modal').addEventListener('click', () => {
            this.hideModal();
        });

        document.getElementById('cancel-btn').addEventListener('click', () => {
            this.hideModal();
        });

        document.getElementById('save-btn').addEventListener('click', () => {
            this.saveTool();
        });

        // 模态框外部点击关闭
        document.getElementById('modal-overlay').addEventListener('click', (e) => {
            if (e.target === e.currentTarget) {
                this.hideModal();
            }
        });

        // 视图切换
        document.querySelectorAll('.view-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const viewType = e.target.closest('.view-btn').dataset.view;
                this.switchView(viewType);
            });
        });

        // 清除筛选
        document.getElementById('clear-filters').addEventListener('click', () => {
            this.clearFilters();
        });

        // 主题切换
        document.getElementById('theme-toggle').addEventListener('click', () => {
            this.toggleTheme();
        });

        // 导出/导入数据
        document.getElementById('export-data').addEventListener('click', () => {
            this.exportData();
        });

        document.getElementById('import-data').addEventListener('click', () => {
            this.importData();
        });

        // 关于按钮
        document.getElementById('about').addEventListener('click', () => {
            this.showAbout();
        });

        // 导航菜单
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleNavigation(e.target.textContent.trim());
            });
        });
    }

    initKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // 搜索快捷键 "/"
            if (e.key === '/' && !e.ctrlKey && !e.metaKey && e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
                e.preventDefault();
                document.getElementById('search-input').focus();
            }

            // 添加工具快捷键 Ctrl+N
            if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
                e.preventDefault();
                this.showModal();
            }

            // ESC 关闭模态框
            if (e.key === 'Escape') {
                this.hideModal();
            }
        });
    }

    generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    saveData(data = null) {
        const dataToSave = data || this.tools;
        localStorage.setItem('linksHub_tools', JSON.stringify(dataToSave));
    }

    handleNavigation(section) {
        // 更新导航状态
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });

        event.target.classList.add('active');

        // 根据导航筛选内容
        switch (section) {
            case '首页':
                this.clearFilters();
                break;
            case '工具':
                this.clearFilters();
                break;
            case '收藏':
                this.showFavorites();
                break;
            case '设置':
                this.showSettings();
                break;
        }
    }

    showFavorites() {
        this.clearFilters();
        this.filteredTools = this.tools.filter(tool => tool.favorited);
        this.render();
    }

    showSettings() {
        const settingsModal = this.createSettingsModal();
        document.body.appendChild(settingsModal);
    }

    createSettingsModal() {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay show';
        modal.innerHTML = `
      <div class="modal">
        <div class="modal-header">
          <h3>设置</h3>
          <button class="btn-icon close-settings">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="2"/>
              <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="2"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>主题设置</label>
            <div style="display: flex; gap: 1rem; margin-top: 0.5rem;">
              <button class="btn-ghost theme-btn ${!this.isDarkTheme ? 'active' : ''}" data-theme="light">浅色主题</button>
              <button class="btn-ghost theme-btn ${this.isDarkTheme ? 'active' : ''}" data-theme="dark">深色主题</button>
            </div>
          </div>
          <div class="form-group">
            <label>数据管理</label>
            <div style="display: flex; gap: 1rem; margin-top: 0.5rem;">
              <button class="btn-ghost" id="export-settings">导出数据</button>
              <button class="btn-ghost" id="import-settings">导入数据</button>
              <button class="btn-ghost" id="clear-all-data" style="color: var(--color-error);">清空数据</button>
            </div>
          </div>
          <div class="form-group">
            <label>统计信息</label>
            <div style="color: var(--color-gray-600); font-size: 0.875rem; line-height: 1.6;">
              <p>总工具数: ${this.tools.length}</p>
              <p>本地工具: ${this.tools.filter(t => t.kind === 'LOCAL').length}</p>
              <p>在线工具: ${this.tools.filter(t => t.kind === 'WEB').length}</p>
              <p>收藏工具: ${this.tools.filter(t => t.favorited).length}</p>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-primary close-settings">完成</button>
        </div>
      </div>
    `;

        // 绑定事件
        modal.querySelectorAll('.close-settings').forEach(btn => {
            btn.addEventListener('click', () => {
                document.body.removeChild(modal);
            });
        });

        modal.querySelectorAll('.theme-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const theme = btn.dataset.theme;
                this.setTheme(theme);
                modal.querySelectorAll('.theme-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            });
        });

        modal.querySelector('#export-settings').addEventListener('click', () => {
            this.exportData();
        });

        modal.querySelector('#import-settings').addEventListener('click', () => {
            this.importData();
        });

        modal.querySelector('#clear-all-data').addEventListener('click', () => {
            if (confirm('确定要清空所有数据吗？此操作不可恢复！')) {
                this.tools = [];
                this.filteredTools = [];
                this.saveData();
                this.render();
                this.updateStats();
                this.renderTagFilters();
                document.body.removeChild(modal);
            }
        });

        return modal;
    }

    setTheme(theme) {
        this.isDarkTheme = theme === 'dark';
        this.applyTheme();
        localStorage.setItem('linksHub_theme', theme);
    }

    applyTheme() {
        if (this.isDarkTheme) {
            document.body.classList.add('dark-theme');
        } else {
            document.body.classList.remove('dark-theme');
        }
    }

    toggleTheme() {
        this.setTheme(this.isDarkTheme ? 'light' : 'dark');
    }

    showModal(tool = null) {
        this.currentEditingId = tool ? tool.id : null;
        const modal = document.getElementById('modal-overlay');
        const title = document.getElementById('modal-title');

        if (tool) {
            title.textContent = '编辑工具';
            document.getElementById('tool-name').value = tool.title;
            document.getElementById('tool-url').value = tool.url;
            document.getElementById('tool-description').value = tool.desc || '';
            document.getElementById('tool-tags').value = Array.isArray(tool.tags) ? tool.tags.join(', ') : (tool.tags || '');
        } else {
            title.textContent = '添加新工具';
            document.getElementById('tool-name').value = '';
            document.getElementById('tool-url').value = '';
            document.getElementById('tool-description').value = '';
            document.getElementById('tool-tags').value = '';
        }

        modal.classList.add('show');
        setTimeout(() => document.getElementById('tool-name').focus(), 100);
    }

    hideModal() {
        document.getElementById('modal-overlay').classList.remove('show');
        this.currentEditingId = null;
    }

    saveTool() {
        const name = document.getElementById('tool-name').value.trim();
        const url = document.getElementById('tool-url').value.trim();
        const description = document.getElementById('tool-description').value.trim();
        const tagsInput = document.getElementById('tool-tags').value.trim();

        if (!name || !url) {
            this.showNotification('请填写工具名称和链接地址', 'error');
            return;
        }

        const tags = tagsInput.split(',').map(tag => tag.trim()).filter(tag => tag);
        const kind = url.startsWith('http') ? 'WEB' : 'LOCAL';

        const toolData = {
            title: name,
            url: url,
            desc: description,
            tags: tags,
            kind: kind,
            online: true,
            favorited: false,
            updatedAt: new Date().toISOString()
        };

        if (this.currentEditingId) {
            // 编辑现有工具
            const index = this.tools.findIndex(t => t.id === this.currentEditingId);
            if (index !== -1) {
                this.tools[index] = { ...this.tools[index], ...toolData };
                this.showNotification('工具更新成功', 'success');
            }
        } else {
            // 添加新工具
            toolData.id = this.generateId();
            toolData.createdAt = new Date().toISOString();
            this.tools.unshift(toolData);
            this.showNotification('工具添加成功', 'success');
        }

        this.saveData();
        this.filteredTools = [...this.tools];
        this.render();
        this.updateStats();
        this.renderTagFilters();
        this.hideModal();
    }

    deleteTool(id) {
        const tool = this.tools.find(t => t.id === id);
        if (!tool) return;

        if (confirm(`确定要删除"${tool.title}"吗？`)) {
            this.tools = this.tools.filter(tool => tool.id !== id);
            this.filteredTools = this.filteredTools.filter(tool => tool.id !== id);
            this.saveData();
            this.render();
            this.updateStats();
            this.renderTagFilters();
            this.showNotification('工具删除成功', 'success');
        }
    }

    toggleFavorite(id) {
        const tool = this.tools.find(t => t.id === id);
        if (tool) {
            tool.favorited = !tool.favorited;
            tool.updatedAt = new Date().toISOString();
            this.saveData();
            this.render();
            this.updateStats();

            const action = tool.favorited ? '添加到收藏' : '取消收藏';
            this.showNotification(`${action}成功`, 'success');
        }
    }

    filterTools(searchTerm = '') {
        const search = searchTerm.toLowerCase();

        this.filteredTools = this.tools.filter(tool => {
            const matchesSearch = !searchTerm ||
                tool.title.toLowerCase().includes(search) ||
                tool.desc.toLowerCase().includes(search) ||
                (Array.isArray(tool.tags) ? tool.tags.join(' ') : tool.tags).toLowerCase().includes(search) ||
                tool.url.toLowerCase().includes(search);

            const matchesFilters = this.activeFilters.size === 0 ||
                [...this.activeFilters].some(filter => {
                    const tags = Array.isArray(tool.tags) ? tool.tags : tool.tags.split(',').map(t => t.trim());
                    return tags.some(tag => tag.toLowerCase().includes(filter.toLowerCase()));
                });

            return matchesSearch && matchesFilters;
        });

        this.render();
    }

    applyTagFilter(tag) {
        if (this.activeFilters.has(tag)) {
            this.activeFilters.delete(tag);
        } else {
            this.activeFilters.add(tag);
        }

        this.renderTagFilters();
        this.filterTools(document.getElementById('search-input').value);
    }

    clearFilters() {
        this.activeFilters.clear();
        document.getElementById('search-input').value = '';
        this.filteredTools = [...this.tools];
        this.renderTagFilters();
        this.render();
    }

    switchView(view) {
        this.currentView = view;
        document.querySelectorAll('.view-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.view === view);
        });

        const grid = document.getElementById('tools-grid');
        if (view === 'list') {
            grid.style.gridTemplateColumns = '1fr';
            grid.classList.add('list-view');
        } else {
            grid.style.gridTemplateColumns = 'repeat(auto-fill, minmax(320px, 1fr))';
            grid.classList.remove('list-view');
        }
    }

    openTool(url) {
        if (url.startsWith('http://') || url.startsWith('https://')) {
            window.open(url, '_blank');
        } else {
            // 本地文件，在当前窗口打开
            window.open(url, '_blank');
        }
    }

    render() {
        const grid = document.getElementById('tools-grid');
        const emptyState = document.getElementById('empty-state');

        if (this.filteredTools.length === 0) {
            grid.style.display = 'none';
            emptyState.style.display = 'block';
            return;
        }

        grid.style.display = 'grid';
        emptyState.style.display = 'none';

        grid.innerHTML = this.filteredTools.map(tool => this.createToolCard(tool)).join('');

        // 绑定卡片事件
        this.bindCardEvents();
    }

    bindCardEvents() {
        const grid = document.getElementById('tools-grid');

        grid.querySelectorAll('.tool-card').forEach(card => {
            const id = card.dataset.id;
            const tool = this.tools.find(t => t.id === id);

            // 点击卡片打开工具
            card.addEventListener('click', (e) => {
                if (!e.target.closest('.tool-actions')) {
                    this.openTool(tool.url);
                }
            });

            // 收藏按钮
            const favBtn = card.querySelector('.fav-btn');
            if (favBtn) {
                favBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.toggleFavorite(id);
                });
            }

            // 编辑按钮
            const editBtn = card.querySelector('.edit-btn');
            if (editBtn) {
                editBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.showModal(tool);
                });
            }

            // 删除按钮
            const deleteBtn = card.querySelector('.delete-btn');
            if (deleteBtn) {
                deleteBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.deleteTool(id);
                });
            }
        });
    }

    createToolCard(tool) {
        const isLocal = tool.kind === 'LOCAL';
        const typeClass = isLocal ? 'local' : 'web';
        const typeText = tool.kind;
        const typeIcon = isLocal ? '📁' : '🌐';

        const tags = Array.isArray(tool.tags) ? tool.tags : (tool.tags ? tool.tags.split(',') : []);
        const tagElements = tags.map(tag =>
            `<span class="tool-tag">${tag.trim()}</span>`
        ).join('');

        const statusIndicator = tool.online ? '' : '<span class="status-offline">离线</span>';
        
        // 调试：打印工具数据
        console.log('Tool data:', tool);
        console.log('Tool desc:', tool.desc);
        
        // 确保描述正确显示 - 修复这里
        const description = (tool.desc && tool.desc.trim() !== '') ? tool.desc : '暂无描述';
        
        console.log('Final description:', description);

        return `
      <div class="tool-card ${tool.favorited ? 'favorited' : ''}" data-id="${tool.id}">
        <div class="tool-header">
          <div class="tool-info">
            <h3>${tool.title} ${statusIndicator}</h3>
            <span class="tool-type ${typeClass}">
              ${typeIcon} ${typeText}
            </span>
          </div>
          <div class="tool-actions">
            <button class="btn-icon fav-btn ${tool.favorited ? 'favorited' : ''}" title="${tool.favorited ? '取消收藏' : '添加收藏'}">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <polygon points="12,2 15.09,8.26 22,9.27 17,14.14 18.18,21.02 12,17.77 5.82,21.02 7,14.14 2,9.27 8.91,8.26" 
                  stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" 
                  fill="${tool.favorited ? 'currentColor' : 'none'}"/>
              </svg>
            </button>
            <button class="btn-icon edit-btn" title="编辑">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" stroke="currentColor" stroke-width="2"/>
                <path d="m18.5 2.5 3 3L12 15l-4 1 1-4 9.5-9.5z" stroke="currentColor" stroke-width="2"/>
              </svg>
            </button>
            <button class="btn-icon delete-btn" title="删除">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <polyline points="3,6 5,6 21,6" stroke="currentColor" stroke-width="2"/>
                <path d="m19,6v14a2,2 0 0,1-2,2H7a2,2 0 0,1-2-2V6m3,0V4a2,2 0 0,1,2-2h4a2,2 0 0,1,2,2v2" stroke="currentColor" stroke-width="2"/>
                <line x1="10" y1="11" x2="10" y2="17" stroke="currentColor" stroke-width="2"/>
                <line x1="14" y1="11" x2="14" y2="17" stroke="currentColor" stroke-width="2"/>
              </svg>
            </button>
          </div>
        </div>
        <div class="tool-url" title="${tool.url}">${this.truncateUrl(tool.url)}</div>
        <div class="tool-description">${description}</div>
        <div class="tool-footer">
          <div class="tool-tags">${tagElements}</div>
        </div>
      </div>
    `;
    }

    truncateUrl(url, maxLength = 50) {
        if (url.length <= maxLength) return url;
        return url.substring(0, maxLength) + '...';
    }

    updateStats() {
        const total = this.tools.length;
        const local = this.tools.filter(t => t.kind === 'LOCAL').length;
        const web = this.tools.filter(t => t.kind === 'WEB').length;
        const favorited = this.tools.filter(t => t.favorited).length;

        this.animateNumber('total-count', total);
        this.animateNumber('local-count', local);
        this.animateNumber('web-count', web);
        this.animateNumber('fav-count', favorited);
    }

    animateNumber(elementId, targetNumber) {
        const element = document.getElementById(elementId);
        const currentNumber = parseInt(element.textContent) || 0;
        const duration = 500;
        const steps = 20;
        const increment = (targetNumber - currentNumber) / steps;

        let current = currentNumber;
        const timer = setInterval(() => {
            current += increment;
            if ((increment > 0 && current >= targetNumber) || (increment < 0 && current <= targetNumber)) {
                element.textContent = targetNumber;
                clearInterval(timer);
            } else {
                element.textContent = Math.round(current);
            }
        }, duration / steps);
    }

    renderTagFilters() {
        const container = document.getElementById('tag-filters');
        const allTags = [...new Set(
            this.tools.flatMap(tool => {
                const tags = Array.isArray(tool.tags) ? tool.tags : (tool.tags ? tool.tags.split(',') : []);
                return tags.map(tag => tag.trim()).filter(tag => tag);
            })
        )];

        if (allTags.length === 0) {
            container.innerHTML = '<p style="color: var(--color-gray-500); font-size: 0.875rem;">暂无标签</p>';
            return;
        }

        container.innerHTML = allTags.map(tag =>
            `<button class="tag-filter ${this.activeFilters.has(tag) ? 'active' : ''}" 
        onclick="app.applyTagFilter('${tag.replace(/'/g, "\\'")}')">${tag}</button>`
        ).join('');
    }

    showNotification(message, type = 'info') {
        // 创建通知元素
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
      <div class="notification-content">
        <span>${message}</span>
        <button class="notification-close">×</button>
      </div>
    `;

        // 添加样式（如果还没有的话）
        if (!document.querySelector('#notification-styles')) {
            const styles = document.createElement('style');
            styles.id = 'notification-styles';
            styles.textContent = `
        .notification {
          position: fixed;
          top: 20px;
          right: 20px;
          background: white;
          border-radius: 8px;
          padding: 16px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
          z-index: 1001;
          transform: translateX(400px);
          transition: transform 0.3s ease;
          border-left: 4px solid var(--color-primary);
        }
        .notification.notification-success {
          border-left-color: var(--color-success);
        }
        .notification.notification-error {
          border-left-color: var(--color-error);
        }
        .notification.notification-warning {
          border-left-color: var(--color-warning);
        }
        .notification.show {
          transform: translateX(0);
        }
        .notification-content {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
        }
        .notification-close {
          background: none;
          border: none;
          font-size: 18px;
          cursor: pointer;
          color: var(--color-gray-400);
        }
        .notification-close:hover {
          color: var(--color-gray-600);
        }
      `;
            document.head.appendChild(styles);
        }

        document.body.appendChild(notification);

        // 显示动画
        setTimeout(() => notification.classList.add('show'), 100);

        // 关闭按钮事件
        notification.querySelector('.notification-close').addEventListener('click', () => {
            this.hideNotification(notification);
        });

        // 自动关闭
        setTimeout(() => {
            if (document.body.contains(notification)) {
                this.hideNotification(notification);
            }
        }, 3000);
    }

    hideNotification(notification) {
        notification.classList.remove('show');
        setTimeout(() => {
            if (document.body.contains(notification)) {
                document.body.removeChild(notification);
            }
        }, 300);
    }

    exportData() {
        const data = {
            tools: this.tools,
            exportDate: new Date().toISOString(),
            version: '2.0',
            totalCount: this.tools.length
        };

        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `links-hub-backup-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        this.showNotification('数据导出成功', 'success');
    }

    importData() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';
        input.onchange = (e) => {
            const file = e.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    const data = JSON.parse(e.target.result);
                    if (data.tools && Array.isArray(data.tools)) {
                        const confirmMessage = `确定要导入 ${data.tools.length} 个工具吗？这将替换现有的 ${this.tools.length} 个工具。`;
                        if (confirm(confirmMessage)) {
                            this.tools = data.tools.map(tool => ({
                                ...tool,
                                id: tool.id || this.generateId(),
                                updatedAt: new Date().toISOString()
                            }));
                            this.filteredTools = [...this.tools];
                            this.clearFilters();
                            this.saveData();
                            this.render();
                            this.updateStats();
                            this.renderTagFilters();
                            this.showNotification(`成功导入 ${data.tools.length} 个工具`, 'success');
                        }
                    } else {
                        this.showNotification('无效的数据格式', 'error');
                    }
                } catch (err) {
                    this.showNotification('文件解析失败：' + err.message, 'error');
                }
            };
            reader.readAsText(file);
        };
        input.click();
    }

    showAbout() {
        const aboutModal = document.createElement('div');
        aboutModal.className = 'modal-overlay show';
        aboutModal.innerHTML = `
      <div class="modal">
        <div class="modal-header">
          <h3>关于 Links Hub</h3>
          <button class="btn-icon close-about">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="2"/>
              <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="2"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div style="text-align: center; margin-bottom: 2rem;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">⚡</div>
            <h2 style="margin-bottom: 0.5rem;">Links Hub v2.0</h2>
            <p style="color: var(--color-gray-600);">一个简洁优雅的工具导航管理器</p>
          </div>
          
          <div style="margin-bottom: 1.5rem;">
            <h4 style="margin-bottom: 0.5rem; color: var(--color-primary);">✨ 主要特性</h4>
            <ul style="color: var(--color-gray-600); line-height: 1.6; padding-left: 1.5rem;">
              <li>本地存储，数据安全可靠</li>
              <li>支持搜索和标签筛选</li>
              <li>Vue.js 风格的现代化界面</li>
              <li>完整的响应式设计</li>
              <li>支持数据导入导出</li>
              <li>快捷键操作支持</li>
            </ul>
          </div>
          
          <div style="margin-bottom: 1.5rem;">
            <h4 style="margin-bottom: 0.5rem; color: var(--color-primary);">⌨️ 快捷键</h4>
            <div style="display: grid; grid-template-columns: auto 1fr; gap: 0.5rem 1rem; color: var(--color-gray-600); font-size: 0.875rem;">
              <kbd style="background: var(--color-gray-100); padding: 0.25rem 0.5rem; border-radius: 4px; font-family: monospace;">/</kbd>
              <span>聚焦搜索框</span>
              <kbd style="background: var(--color-gray-100); padding: 0.25rem 0.5rem; border-radius: 4px; font-family: monospace;">Ctrl+N</kbd>
              <span>添加新工具</span>
              <kbd style="background: var(--color-gray-100); padding: 0.25rem 0.5rem; border-radius: 4px; font-family: monospace;">ESC</kbd>
              <span>关闭模态框</span>
            </div>
          </div>
          
          <div style="text-align: center; padding-top: 1rem; border-top: 1px solid var(--color-gray-200); color: var(--color-gray-500); font-size: 0.875rem;">
            <p>© 2025 Links Hub. 本地存储，保护您的隐私。</p>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-primary close-about">了解了</button>
        </div>
      </div>
    `;

        document.body.appendChild(aboutModal);

        aboutModal.querySelectorAll('.close-about').forEach(btn => {
            btn.addEventListener('click', () => {
                document.body.removeChild(aboutModal);
            });
        });

        aboutModal.addEventListener('click', (e) => {
            if (e.target === aboutModal) {
                document.body.removeChild(aboutModal);
            }
        });
    }
}

// 初始化应用
const app = new LinksHub();

// 导出到全局作用域，供HTML中的onclick使用
window.app = app;