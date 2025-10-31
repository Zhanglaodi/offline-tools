class LinksHub {
    constructor() {
        this.tools = JSON.parse(localStorage.getItem('linksHub_tools') || '[]');
        this.filteredTools = [...this.tools];
        this.currentView = 'grid';
        this.activeFilters = new Set();
        this.currentEditingId = null;

        this.init();
    }

    init() {
        this.bindEvents();
        this.render();
        this.updateStats();
        this.renderTagFilters();
        this.initKeyboardShortcuts();

        // 如果没有数据，添加一些示例数据
        if (this.tools.length === 0) {
            this.addSampleData();
        }
    }

    bindEvents() {
        // 搜索功能
        document.getElementById('search-input').addEventListener('input', (e) => {
            this.filterTools(e.target.value);
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
                this.switchView(e.target.closest('.view-btn').dataset.view);
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
    }

    initKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // 搜索快捷键 "/"
            if (e.key === '/' && !e.ctrlKey && !e.metaKey) {
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

    addSampleData() {
        const sampleTools = [
            {
                id: this.generateId(),
                title: 'DBC 编写工具',
                url: './tools/dbc_editor/index.html',
                description: '本地页面：修复跨行注释的 DBC 可视化。',
                tags: 'CAN,DBC,前端',
                favorited: false,
                createdAt: new Date().toISOString()
            },
            {
                id: this.generateId(),
                title: '进制转换工具',
                url: './tools/base_converter/index.html',
                description: '进制之间互转',
                tags: '进制,工具',
                favorited: false,
                createdAt: new Date().toISOString()
            },
            {
                id: this.generateId(),
                title: '波特率计算工具',
                url: './tools/baud_rate/index.html',
                description: '波特率计算',
                tags: '波特率,调试',
                favorited: false,
                createdAt: new Date().toISOString()
            },
            {
                id: this.generateId(),
                title: '创芯曲线工具',
                url: './tools/创芯科技/index.html',
                description: '创新科技曲线工具，仅支持 CSV 文件',
                tags: '曲线,创芯,工具',
                favorited: false,
                createdAt: new Date().toISOString()
            },
            {
                id: this.generateId(),
                title: '周立功曲线工具',
                url: './tools/周立功/index.html',
                description: '支持解析 ASC 文件',
                tags: '曲线,周立功,工具',
                favorited: false,
                createdAt: new Date().toISOString()
            },
            {
                id: this.generateId(),
                title: '串口工具-网页',
                url: './tools/serial/index.html',
                description: '串口工具，仅供娱乐',
                tags: '串口,工具',
                favorited: false,
                createdAt: new Date().toISOString()
            },
            {
                id: this.generateId(),
                title: '塞弗转向-计算轮距',
                url: './tools/塞弗转向-计算轮距/index.html',
                description: '塞弗转向轮距计算工具',
                tags: '汽车,工具',
                favorited: false,
                createdAt: new Date().toISOString()
            },
            {
                id: this.generateId(),
                title: 'CRC 校验工具',
                url: './tools/CRC-校验/index.html',
                description: '支持自定义多项式，支持多种 CRC 校验',
                tags: 'CRC,校验,工具',
                favorited: false,
                createdAt: new Date().toISOString()
            },
            {
                id: this.generateId(),
                title: 'BCC 校验工具',
                url: './tools/BCC校验/index.html',
                description: '支持 BCC 校验',
                tags: 'BCC,校验,工具',
                favorited: false,
                createdAt: new Date().toISOString()
            },
            {
                id: this.generateId(),
                title: 'STM32 文档 (F4 HAL)',
                url: 'https://www.st.com/en/embedded-software/stm32cube-mcu-packages.html',
                description: 'F4 HAL 参考与例程入口',
                tags: 'STM32,HAL,文档',
                favorited: false,
                createdAt: new Date().toISOString()
            },
            {
                id: this.generateId(),
                title: 'ASC 曲线工具（独立运行版）',
                url: 'https://pan.baidu.com/s/5iUl1EJqsuVKNUqp-m0dtJg',
                description: 'ASC 文件曲线工具',
                tags: 'ZLG,曲线,汽车',
                favorited: false,
                createdAt: new Date().toISOString()
            }
        ];

        this.tools = sampleTools;
        this.filteredTools = [...this.tools];
        this.saveData();
    }

    generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    saveData() {
        localStorage.setItem('linksHub_tools', JSON.stringify(this.tools));
    }

    showModal(tool = null) {
        this.currentEditingId = tool ? tool.id : null;
        const modal = document.getElementById('modal-overlay');
        const title = document.getElementById('modal-title');

        if (tool) {
            title.textContent = '编辑工具';
            document.getElementById('tool-name').value = tool.title;
            document.getElementById('tool-url').value = tool.url;
            document.getElementById('tool-description').value = tool.description || '';
            document.getElementById('tool-tags').value = tool.tags || '';
        } else {
            title.textContent = '添加新工具';
            document.getElementById('tool-name').value = '';
            document.getElementById('tool-url').value = '';
            document.getElementById('tool-description').value = '';
            document.getElementById('tool-tags').value = '';
        }

        modal.classList.add('show');
        document.getElementById('tool-name').focus();
    }

    hideModal() {
        document.getElementById('modal-overlay').classList.remove('show');
        this.currentEditingId = null;
    }

    saveTool() {
        const name = document.getElementById('tool-name').value.trim();
        const url = document.getElementById('tool-url').value.trim();
        const description = document.getElementById('tool-description').value.trim();
        const tags = document.getElementById('tool-tags').value.trim();

        if (!name || !url) {
            alert('请填写工具名称和链接地址');
            return;
        }

        const toolData = {
            title: name,
            url: url,
            description: description,
            tags: tags,
            favorited: false,
            updatedAt: new Date().toISOString()
        };

        if (this.currentEditingId) {
            // 编辑现有工具
            const index = this.tools.findIndex(t => t.id === this.currentEditingId);
            if (index !== -1) {
                this.tools[index] = { ...this.tools[index], ...toolData };
            }
        } else {
            // 添加新工具
            toolData.id = this.generateId();
            toolData.createdAt = new Date().toISOString();
            this.tools.unshift(toolData);
        }

        this.saveData();
        this.filteredTools = [...this.tools];
        this.render();
        this.updateStats();
        this.renderTagFilters();
        this.hideModal();
    }

    deleteTool(id) {
        if (confirm('确定要删除这个工具吗？')) {
            this.tools = this.tools.filter(tool => tool.id !== id);
            this.filteredTools = this.filteredTools.filter(tool => tool.id !== id);
            this.saveData();
            this.render();
            this.updateStats();
            this.renderTagFilters();
        }
    }

    toggleFavorite(id) {
        const tool = this.tools.find(t => t.id === id);
        if (tool) {
            tool.favorited = !tool.favorited;
            this.saveData();
            this.render();
            this.updateStats();
        }
    }

    filterTools(searchTerm = '') {
        const search = searchTerm.toLowerCase();

        this.filteredTools = this.tools.filter(tool => {
            const matchesSearch = !searchTerm ||
                tool.title.toLowerCase().includes(search) ||
                tool.description.toLowerCase().includes(search) ||
                tool.tags.toLowerCase().includes(search) ||
                tool.url.toLowerCase().includes(search);

            const matchesFilters = this.activeFilters.size === 0 ||
                [...this.activeFilters].some(filter =>
                    tool.tags.toLowerCase().includes(filter.toLowerCase())
                );

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
        } else {
            grid.style.gridTemplateColumns = 'repeat(auto-fill, minmax(320px, 1fr))';
        }
    }

    openTool(url) {
        if (url.startsWith('http://') || url.startsWith('https://')) {
            window.open(url, '_blank');
        } else {
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
        const isLocal = !tool.url.startsWith('http');
        const typeClass = isLocal ? 'local' : 'web';
        const typeText = isLocal ? 'LOCAL' : 'WEB';
        const typeIcon = isLocal ? '📁' : '🌐';

        const tags = tool.tags ? tool.tags.split(',').map(tag =>
            `<span class="tool-tag">${tag.trim()}</span>`
        ).join('') : '';

        return `
      <div class="tool-card ${tool.favorited ? 'favorited' : ''}" data-id="${tool.id}">
        <div class="tool-header">
          <div class="tool-info">
            <h3>${tool.title}</h3>
            <span class="tool-type ${typeClass}">
              ${typeIcon} ${typeText}
            </span>
          </div>
          <div class="tool-actions">
            <button class="btn-icon fav-btn ${tool.favorited ? 'favorited' : ''}" title="收藏">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <polygon points="12,2 15.09,8.26 22,9.27 17,14.14 18.18,21.02 12,17.77 5.82,21.02 7,14.14 2,9.27 8.91,8.26" 
                  stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" 
                  fill="${tool.favorited ? 'currentColor' : 'none'}"/>
              </svg>
            </button>
            <button class="btn-icon edit-btn" title="编辑">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="m18 2 4 4-6 6-4-4 6-6z" stroke="currentColor" stroke-width="2"/>
                <path d="m22 6-4-4-6 6 4 4 6-6z" stroke="currentColor" stroke-width="2"/>
                <path d="M2 20h4l10-10-4-4L2 16v4z" stroke="currentColor" stroke-width="2"/>
              </svg>
            </button>
            <button class="btn-icon delete-btn" title="删除">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <polyline points="3,6 5,6 21,6" stroke="currentColor" stroke-width="2"/>
                <path d="m19,6v14a2,2 0 0,1-2,2H7a2,2 0 0,1-2-2V6m3,0V4a2,2 0 0,1,2-2h4a2,2 0 0,1,2,2v2" stroke="currentColor" stroke-width="2"/>
              </svg>
            </button>
          </div>
        </div>
        <div class="tool-url">${tool.url}</div>
        <div class="tool-description">${tool.description || '暂无描述'}</div>
        <div class="tool-footer">
          <div class="tool-tags">${tags}</div>
        </div>
      </div>
    `;
    }

    updateStats() {
        const total = this.tools.length;
        const local = this.tools.filter(t => !t.url.startsWith('http')).length;
        const web = this.tools.filter(t => t.url.startsWith('http')).length;
        const favorited = this.tools.filter(t => t.favorited).length;

        document.getElementById('total-count').textContent = total;
        document.getElementById('local-count').textContent = local;
        document.getElementById('web-count').textContent = web;
        document.getElementById('fav-count').textContent = favorited;
    }

    renderTagFilters() {
        const container = document.getElementById('tag-filters');
        const allTags = [...new Set(
            this.tools.flatMap(tool =>
                tool.tags ? tool.tags.split(',').map(tag => tag.trim()) : []
            )
        )].filter(tag => tag);

        container.innerHTML = allTags.map(tag =>
            `<button class="tag-filter ${this.activeFilters.has(tag) ? 'active' : ''}" 
        onclick="app.applyTagFilter('${tag}')">${tag}</button>`
        ).join('');
    }

    toggleTheme() {
        // 简单的主题切换实现
        document.body.classList.toggle('dark-theme');
        localStorage.setItem('linksHub_theme', document.body.classList.contains('dark-theme') ? 'dark' : 'light');
    }

    exportData() {
        const data = {
            tools: this.tools,
            exportDate: new Date().toISOString(),
            version: '2.0'
        };

        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `links-hub-backup-${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        URL.revokeObjectURL(url);
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
                        if (confirm('确定要导入数据吗？这将覆盖现有数据。')) {
                            this.tools = data.tools;
                            this.filteredTools = [...this.tools];
                            this.saveData();
                            this.render();
                            this.updateStats();
                            this.renderTagFilters();
                            alert('数据导入成功！');
                        }
                    } else {
                        alert('无效的数据格式');
                    }
                } catch (err) {
                    alert('文件解析失败：' + err.message);
                }
            };
            reader.readAsText(file);
        };
        input.click();
    }

    showAbout() {
        alert(`Links Hub v2.0
    
一个简洁的工具导航管理器
    
• 本地存储，数据安全
• 支持搜索和标签筛选
• 响应式设计
• Vue.js 风格界面

快捷键：
• / : 聚焦搜索框
• Ctrl+N : 添加新工具
• ESC : 关闭模态框`);
    }
}

// 初始化应用
const app = new LinksHub();

// 加载主题
const savedTheme = localStorage.getItem('linksHub_theme');
if (savedTheme === 'dark') {
    document.body.classList.add('dark-theme');
}