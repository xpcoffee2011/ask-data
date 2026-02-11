# 智能问数 (Ask Data)

基于Claude AI的智能数据库问答系统，支持用自然语言查询数据库。

## 功能特性

- 🤖 使用Claude AI将自然语言转换为SQL查询
- 💾 支持多种数据库（MySQL, PostgreSQL, SQLite等）
- 🔍 自动分析数据库表结构
- 📊 智能结果解析和展示
- 🛡️ SQL注入防护和查询安全检查

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 到 `.env` 并填入你的配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：
- `ANTHROPIC_API_KEY`: 你的Claude API密钥
- `DATABASE_URL`: 数据库连接URL

### 3. 运行

```bash
python main.py
```

## 使用示例

```python
from ask_data import AskData

# 初始化
asker = AskData(database_url="sqlite:///example.db")

# 用自然语言提问
result = asker.ask("显示销售额最高的前10个产品")
print(result)
```

## 项目结构

```
ask-data/
├── main.py              # 主程序入口
├── config.py            # 配置管理
├── requirements.txt     # 依赖列表
├── .env.example         # 环境变量示例
├── src/
│   ├── __init__.py
│   ├── database/        # 数据库模块
│   │   ├── __init__.py
│   │   ├── connector.py # 数据库连接
│   │   └── schema.py    # Schema分析
│   ├── llm/            # LLM模块
│   │   ├── __init__.py
│   │   ├── claude.py    # Claude API交互
│   │   └── prompts.py   # 提示词模板
│   ├── sql/            # SQL处理模块
│   │   ├── __init__.py
│   │   ├── generator.py # SQL生成
│   │   ├── executor.py  # SQL执行
│   │   └── validator.py # SQL验证
│   └── core/           # 核心模块
│       ├── __init__.py
│       └── asker.py     # 主逻辑
└── examples/           # 示例代码
    └── example_data.sql
```

## 配置说明

### 数据库连接

默认使用MySQL数据库，URL格式：
```
mysql+pymysql://user:password@localhost:3306/dbname
```

也支持其他数据库：
- PostgreSQL: `postgresql://user:password@localhost:5432/dbname`
- SQLite: `sqlite:///path/to/database.db`

### 初始化示例数据

可以使用 `examples/example_data.sql` 创建示例表和数据：

```bash
mysql -u your_user -p your_database < examples/example_data.sql
```

## 注意事项

- 确保数据库用户有足够的查询权限
- 系统默认只允许SELECT查询，禁止修改数据
- API调用会产生费用，请合理使用
