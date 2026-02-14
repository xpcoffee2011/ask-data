document.addEventListener('DOMContentLoaded', () => {
    const chatContainer = document.getElementById('chat-container');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const examplesList = document.getElementById('examples-list');
    const clearChatBtn = document.getElementById('clear-chat');
    const settingsBtn = document.getElementById('settings-btn');
    const settingsModal = document.getElementById('settings-modal');
    const closeSettings = document.getElementById('close-settings');
    const saveSettings = document.getElementById('save-settings');

    // 默认大模型参数
    let llmConfig = {
        model: localStorage.getItem('llm_model') || 'qwen-max',
        temperature: parseFloat(localStorage.getItem('llm_temp')) || 0.0,
        max_tokens: parseInt(localStorage.getItem('llm_max_tokens')) || 2000
    };

    // 自动调整输入框高度
    userInput.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });


    // 加载示例问题
    async function loadExamples() {
        try {
            const response = await fetch('/api/examples');
            const examples = await response.json();

            examplesList.innerHTML = '';
            examples.forEach(ex => {
                const item = document.createElement('div');
                item.className = 'example-item';
                item.innerHTML = `
                    <h4>${ex.title}</h4>
                    <p>${ex.question}</p>
                `;
                item.onclick = () => {
                    userInput.value = ex.question;
                    userInput.focus();
                    userInput.dispatchEvent(new Event('input'));
                };
                examplesList.appendChild(item);
            });
        } catch (error) {
            console.error('Failed to load examples:', error);
            examplesList.innerHTML = '<p class="muted">无法加载示例</p>';
        }
    }

    // 实用工具：延时函数
    const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

    // 发送消息 (流式)
    async function sendMessage() {
        const question = userInput.value.trim();
        if (!question) return;

        // 清空输入
        userInput.value = '';
        userInput.style.height = 'auto';

        // 移除欢迎界面
        const welcome = document.querySelector('.chat-welcome');
        if (welcome) welcome.remove();

        // 添加用户消息
        addMessage(question, 'user');

        // 添加机器人容器
        const botMsg = addMessage('', 'bot', false);
        const botBubble = botMsg.querySelector('.msg-bubble');
        botBubble.style.display = 'none'; // 隐藏初始空气泡，直接显示卡片

        // 立即展示第一步的标题和正在生成状态
        const initialCard = ensureResultCard(botMsg, '');
        const sqlSpan = initialCard.querySelector('.result-header span');
        const originalSqlHtml = sqlSpan.innerHTML;
        sqlSpan.innerHTML += ` <span class="header-status"><i class="fas fa-spinner fa-spin"></i> 正在生成...</span>`;

        let sql = '';
        let resultCard = initialCard; // 之后直接使用这个卡片
        let explanationText = '';
        let explanationDiv = null;
        let expSpanRef = null;
        let expHeaderOriginalHtml = '';

        try {
            const response = await fetch('/api/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question,
                    config: llmConfig // 传递自定义配置
                })
            });


            if (!response.ok) throw new Error('网络响应错误');

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n\n');
                buffer = lines.pop();

                for (const line of lines) {
                    if (!line.startsWith('data: ')) continue;
                    const event = JSON.parse(line.trim().slice(6));

                    switch (event.type) {
                        case 'sql':
                            sql = event.content;
                            // 更新 SQL 内容
                            const sqlBlock = resultCard.querySelector('.sql-block');
                            sqlBlock.textContent = sql;
                            sqlBlock.classList.add('reveal');

                            const sqlSpanUpdate = resultCard.querySelector('.result-header span');
                            const baseSqlHtml = `<i class="fas fa-magic"></i> 自然语言转化为 SQL`;

                            await sleep(500);
                            sqlSpanUpdate.innerHTML = baseSqlHtml; // 任务完成，移除“正在生成”
                            break;

                        case 'data':
                            const { data, columns } = event.content;
                            const cardForData = botMsg.querySelector('.result-card');
                            updateResultCard(botMsg, columns, data);

                            const dataHeader = cardForData.querySelector('.data-header');
                            const dataSpan = dataHeader.querySelector('span');
                            const originalDataHtml = dataSpan.innerHTML;
                            dataSpan.innerHTML += ` <span class="header-status"><i class="fas fa-spinner fa-spin"></i> 正在检索...</span>`;

                            await sleep(500); // 缩短延时
                            // 移除检索提示，但保留带行数的标题
                            dataSpan.innerHTML = ` <i class="fas fa-table"></i> 数据检索结果 (${data ? data.length : 0} 条)`;
                            break;

                        case 'explanation_start':
                            // 隐藏正在生成的提示泡泡，转而在卡片中展示
                            botBubble.style.display = 'none';
                            const cardForExp = botMsg.querySelector('.result-card');
                            if (cardForExp) {
                                const expHeader = cardForExp.querySelector('.explanation-header');
                                explanationDiv = cardForExp.querySelector('.explanation-content');
                                if (expHeader) {
                                    expHeader.style.display = 'flex';
                                    expHeader.classList.add('reveal');
                                    expSpanRef = expHeader.querySelector('span');
                                    expHeaderOriginalHtml = expSpanRef.innerHTML;
                                    expSpanRef.innerHTML += ` <span class="header-status"><i class="fas fa-spinner fa-spin"></i> 正在生成...</span>`;
                                }
                                if (explanationDiv) {
                                    explanationDiv.style.display = 'block';
                                    explanationDiv.innerHTML = '<div class="typing-sm"><span></span><span></span><span></span></div>';
                                }
                            }
                            break;

                        case 'explanation_chunk':
                            if (explanationDiv) {
                                if (explanationText === '') explanationDiv.innerHTML = ''; // 收到第一个块时移除打字动画
                                explanationText += event.content;
                                // 使用 marked 解析 markdown，并渲染为 HTML
                                explanationDiv.innerHTML = marked.parse(explanationText);
                                // 核心优化：即便数据已经积压，也强制以 30ms 的间隔输出，找回流式体感
                                await sleep(30);
                            }
                            scrollToBottom();
                            break;

                        case 'error':
                            botBubble.style.display = 'block';
                            botBubble.innerHTML = `<div class="error-msg">❌ 出错了: ${event.content}</div>`;
                            // 移除加载状态
                            resultCard.querySelectorAll('.header-status').forEach(s => s.remove());
                            // 如果还没有生成 SQL，隐藏结果卡显示
                            if (!sql) {
                                resultCard.style.display = 'none';
                            }
                            break;
                    }
                }
            }

            // SSE 加载完毕后的终态处理
            if (expSpanRef) {
                expSpanRef.innerHTML = `<i class="fas fa-lightbulb"></i> 数据结果解释`;
            }
        } catch (error) {
            console.error('SSE Error:', error);
            botBubble.style.display = 'block';
            botBubble.innerHTML = `<div class="error-msg">❌ 请求失败: ${error.message}</div>`;
            if (resultCard) {
                resultCard.querySelectorAll('.header-status').forEach(s => s.remove());
                if (!sql) resultCard.style.display = 'none';
            }
        }
    }

    function ensureResultCard(msgDiv, sql) {
        let card = msgDiv.querySelector('.result-card');
        if (!card) {
            card = document.createElement('div');
            card.className = 'result-card';
            msgDiv.appendChild(card);
        }
        card.innerHTML = `
            <div class="result-header reveal">
                <span><i class="fas fa-magic"></i> 自然语言转化为 SQL</span>
            </div>
            <div class="sql-block ${sql ? 'reveal' : ''}" style="${sql ? '' : ''}">${sql}</div>
            <div class="result-header data-header" style="display:none">
                <span><i class="fas fa-table"></i> 数据检索结果</span>
            </div>
            <div class="table-wrapper reveal"></div>
            <div class="result-header explanation-header" style="display:none">
                <span><i class="fas fa-lightbulb"></i> 数据结果解释</span>
            </div>
            <div class="explanation-content" style="display:none"></div>
        `;
        return card;
    }

    function updateResultCard(msgDiv, columns, data) {
        const card = msgDiv.querySelector('.result-card');
        if (!card) return;

        const dataHeader = card.querySelector('.data-header');
        const wrapper = card.querySelector('.table-wrapper');

        dataHeader.style.display = 'flex';
        dataHeader.classList.add('reveal');
        wrapper.innerHTML = renderTable(columns, data);
        wrapper.classList.add('reveal');
        scrollToBottom();
    }

    function addMessage(text, type, isLoading = false) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${type}`;

        let content = '';
        if (isLoading) {
            content = `<div class="msg-bubble"><div class="typing"><span></span><span></span><span></span></div></div>`;
        } else {
            content = `<div class="msg-bubble">${text}</div>`;
        }

        msgDiv.innerHTML = content;
        chatContainer.appendChild(msgDiv);
        scrollToBottom();
        return msgDiv;
    }

    function addBotResponse(result) {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message bot';

        // 第一部分：回答/解释
        let html = `<div class="msg-bubble">${result.explanation || '这是我为你找到的数据：'}</div>`;

        // 第二部分：数据展示卡片
        html += `
            <div class="result-card">
                <div class="result-header">
                    <span><i class="fas fa-code"></i> 生成的 SQL</span>
                </div>
                <div class="sql-block">${result.sql}</div>
                
                <div class="result-header">
                    <span><i class="fas fa-table"></i> 查询结果 (${result.data ? result.data.length : 0} 条)</span>
                </div>
                <div class="table-wrapper">
                    ${renderTable(result.columns, result.data)}
                </div>
            </div>
        `;

        msgDiv.innerHTML = html;
        chatContainer.appendChild(msgDiv);
        scrollToBottom();
    }

    function renderTable(columns, data) {
        if (!data || data.length === 0) return '<div style="padding: 1rem; color: var(--text-muted);">无返回数据</div>';

        let html = '<table><thead><tr>';
        columns.forEach(col => html += `<th>${col}</th>`);
        html += '</tr></thead><tbody>';

        data.forEach(row => {
            html += '<tr>';
            columns.forEach(col => {
                const cell = row[col];
                html += `<td>${cell === null || cell === undefined ? '<span class="muted">null</span>' : cell}</td>`;
            });
            html += '</tr>';
        });

        html += '</tbody></table>';
        return html;
    }

    function scrollToBottom() {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // 事件监听
    sendBtn.onclick = sendMessage;
    userInput.onkeydown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    clearChatBtn.onclick = () => {
        chatContainer.innerHTML = '';
        // 恢复欢迎界面
        const welcome = document.createElement('div');
        welcome.className = 'chat-welcome';
        welcome.innerHTML = `
            <div class="welcome-icon"><i class="fas fa-robot"></i></div>
            <h1>欢迎使用智能问数</h1>
            <p>你可以直接用自然语言向我提问，我会为你生成 SQL 并查询数据库。</p>
        `;
        chatContainer.appendChild(welcome);
    };

    // 加载数据库架构
    async function loadSchema() {
        const explorer = document.getElementById('db-explorer');
        try {
            const response = await fetch('/api/full_schema');
            const schema = await response.json();

            explorer.innerHTML = '';

            Object.keys(schema.tables).forEach(tableName => {
                const tableInfo = schema.tables[tableName];
                const node = document.createElement('div');
                node.className = 'table-node';

                const header = document.createElement('div');
                header.className = 'table-name';
                header.innerHTML = `<i class="fas fa-chevron-right"></i> <span>${tableName}</span>`;

                const colList = document.createElement('div');
                colList.className = 'column-list';

                tableInfo.columns.forEach(col => {
                    const colItem = document.createElement('div');
                    colItem.className = 'column-item';
                    colItem.innerHTML = `
                        <span>${col.name}</span>
                        <span class="column-type">${col.type}</span>
                    `;
                    colList.appendChild(colItem);
                });

                // 添加示例数据预览 (Demo 特色)
                if (tableInfo.sample_data && tableInfo.sample_data.length > 0) {
                    const subTitle = document.createElement('div');
                    subTitle.className = 'explorer-sub-title';
                    subTitle.innerHTML = '<i class="fas fa-table"></i> 表数据';
                    colList.appendChild(subTitle);

                    const miniTable = document.createElement('div');
                    miniTable.className = 'mini-table-wrapper';

                    const keys = Object.keys(tableInfo.sample_data[0]);
                    let tableHtml = '<table class="mini-table"><thead><tr>';
                    keys.forEach(k => tableHtml += `<th>${k}</th>`);
                    tableHtml += '</tr></thead><tbody>';

                    tableInfo.sample_data.forEach(row => {
                        tableHtml += '<tr>';
                        keys.forEach(k => {
                            let val = row[k];
                            if (val === null) val = 'null';
                            tableHtml += `<td>${val}</td>`;
                        });
                        tableHtml += '</tr>';
                    });
                    tableHtml += '</tbody></table>';
                    miniTable.innerHTML = tableHtml;
                    colList.appendChild(miniTable);
                }

                header.onclick = () => {
                    header.classList.toggle('expanded');
                    colList.classList.toggle('show');
                };

                node.appendChild(header);
                node.appendChild(colList);
                explorer.appendChild(node);
            });
        } catch (error) {
            console.error('Failed to load schema:', error);
            explorer.innerHTML = '<p class="muted">无法加载库结构</p>';
        }
    }

    // 设置弹窗逻辑
    settingsBtn.onclick = () => {
        document.getElementById('setting-model').value = llmConfig.model;
        document.getElementById('setting-temp').value = llmConfig.temperature;
        document.getElementById('temp-val').innerText = llmConfig.temperature;
        document.getElementById('setting-max-tokens').value = llmConfig.max_tokens;
        settingsModal.style.display = 'block';
    };

    closeSettings.onclick = () => {
        settingsModal.style.display = 'none';
    };

    document.getElementById('setting-temp').oninput = function () {
        document.getElementById('temp-val').innerText = this.value;
    };

    saveSettings.onclick = () => {
        llmConfig.model = document.getElementById('setting-model').value;
        llmConfig.temperature = parseFloat(document.getElementById('setting-temp').value);
        llmConfig.max_tokens = parseInt(document.getElementById('setting-max-tokens').value);

        localStorage.setItem('llm_model', llmConfig.model);
        localStorage.setItem('llm_temp', llmConfig.temperature);
        localStorage.setItem('llm_max_tokens', llmConfig.max_tokens);

        settingsModal.style.display = 'none';

        const tip = document.createElement('div');
        tip.style = "position:fixed; top:20px; left:50%; transform:translateX(-50%); background:var(--primary); color:white; padding:10px 20px; border-radius:30px; z-index:1000; box-shadow:0 4px 15px rgba(0,0,0,0.3); font-weight:600; font-size: 0.875rem;";
        tip.innerText = "✅ 设置已保存至本地";
        document.body.appendChild(tip);
        setTimeout(() => tip.remove(), 2000);
    };

    window.onclick = (event) => {
        if (event.target == settingsModal) {
            settingsModal.style.display = 'none';
        }
    };

    // 初始化加载
    loadExamples();
    loadSchema();
});
