document.addEventListener('DOMContentLoaded', () => {
    const chatContainer = document.getElementById('chat-container');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const examplesList = document.getElementById('examples-list');
    const clearChatBtn = document.getElementById('clear-chat');

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

    // 发送消息
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
        const botMsg = addMessage('', 'bot', true);
        const botBubble = botMsg.querySelector('.msg-bubble');

        let sql = '';
        let resultCard = null;
        let explanationText = '';
        let explanationDiv = null;

        try {
            const response = await fetch('/api/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question })
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
                            // 移除加载动画，显示状态
                            botBubble.innerHTML = `<div class="status-msg"><i class="fas fa-spinner fa-spin"></i> 正在执行 SQL...</div>`;
                            ensureResultCard(botMsg, sql);
                            break;

                        case 'data':
                            const { data, columns } = event.content;
                            botBubble.innerHTML = `<div class="status-msg"><i class="fas fa-spinner fa-spin"></i> 数据已获取，正在生成解释...</div>`;
                            updateResultCard(botMsg, columns, data);
                            break;

                        case 'explanation_start':
                            botBubble.innerHTML = ''; // 清空状态消息，准备填入解释
                            explanationDiv = document.createElement('div');
                            explanationDiv.className = 'explanation-stream';
                            botBubble.appendChild(explanationDiv);
                            break;

                        case 'explanation_chunk':
                            explanationText += event.content;
                            if (explanationDiv) explanationDiv.textContent = explanationText;
                            scrollToBottom();
                            break;

                        case 'error':
                            botBubble.innerHTML = `<div class="error-msg">❌ 出错了: ${event.content}</div>`;
                            break;
                    }
                }
            }
        } catch (error) {
            console.error('SSE Error:', error);
            botBubble.innerHTML = `<div class="error-msg">❌ 请求失败: ${error.message}</div>`;
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
            <div class="result-header">
                <span><i class="fas fa-code"></i> 生成的 SQL</span>
            </div>
            <div class="sql-block">${sql}</div>
            <div class="result-header data-header" style="display:none">
                <span><i class="fas fa-table"></i> 查询结果</span>
            </div>
            <div class="table-wrapper"></div>
        `;
        return card;
    }

    function updateResultCard(msgDiv, columns, data) {
        const card = msgDiv.querySelector('.result-card');
        if (!card) return;

        const dataHeader = card.querySelector('.data-header');
        const wrapper = card.querySelector('.table-wrapper');

        dataHeader.style.display = 'flex';
        dataHeader.innerHTML = `<span><i class="fas fa-table"></i> 查询结果 (${data ? data.length : 0} 条)</span>`;
        wrapper.innerHTML = renderTable(columns, data);
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
                    subTitle.innerHTML = '<i class="fas fa-table"></i> 示例数据 (Top 5)';
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

    // 初始化加载
    loadExamples();
    loadSchema();
});
