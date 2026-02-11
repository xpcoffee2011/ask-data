"""提示词模板模块"""


def get_text_to_sql_prompt(question: str, schema: str, examples: str = "") -> str:
    """
    生成Text-to-SQL的提示词

    Args:
        question: 用户的自然语言问题
        schema: 数据库schema描述
        examples: 可选的示例

    Returns:
        完整的提示词
    """
    prompt = f"""你是一个专业的 SQL 执行专家。请根据用户的问题和数据库结构，生成一条**纯净、准确、可直接执行**的 SQL 查询语句。

{schema}

注意：每个表都提供了“示例数据”。请通过观察这些真实数据来理解列的含义及常见的列值格式。

要求:
1. 只生成 SELECT 查询。
2. **严禁包含任何解释文字、建议、备注或提醒**（如“注意：请替换库名”等）。如果包含这些非 SQL 文字，系统将崩溃。
3. 只能返回 SQL 语句本身，不要添加 markdown 代码块标签（如 ```sql）。
4. **数据库环境适配**:
   - 如果用户询问库中有多少张表（针对 MySQL），请使用: `SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE();`
   - 不要试图硬编码数据库名称，始终使用 `DATABASE()` 函数获取当前库名。
5. 统计表中记录的数量（如 COUNT(*)）是有效的业务查询。
6. 如果问题确实无法转换为 SQL，仅返回: `ERROR: [原因说明]`

{examples}

用户问题: {question}

SQL查询语句:"""

    return prompt


def get_result_explanation_prompt(question: str, sql: str, results: str) -> str:
    """
    生成结果解释的提示词

    Args:
        question: 用户的原始问题
        sql: 执行的SQL语句
        results: 查询结果

    Returns:
        完整的提示词
    """
    prompt = f"""请用简洁、易懂的自然语言解释以下SQL查询结果。

用户问题: {question}

执行的SQL: {sql}

查询结果:
{results}

请用1-3句话总结这个结果，重点关注:
1. 回答了用户的问题
2. 结果中的关键信息
3. 如果有特殊情况（如空结果、异常数据），需要说明

解释:"""

    return prompt


# 示例查询（可以根据实际数据库添加）
EXAMPLES = """
示例:
问题: 数据库里有多少张表？
SQL: SELECT COUNT(*) as table_count FROM sqlite_master WHERE type='table';

问题: 显示所有用户的数量
SQL: SELECT COUNT(*) as user_count FROM users;

问题: 找出销售额最高的5个产品
SQL: SELECT product_name, sales FROM products ORDER BY sales DESC LIMIT 5;

问题: 计算每个分类的平均价格
SQL: SELECT category, AVG(price) as avg_price FROM products GROUP BY category;
"""
