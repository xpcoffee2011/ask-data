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
    prompt = f"""你是一个专业的SQL专家。请根据用户的问题和数据库结构，生成准确的SQL查询语句。

{schema}

注意：每个表都提供了“示例数据”。请通过观察这些真实数据来理解列的含义、常见的值格式（如日期、状态码等）以及数据之间的关联关系，从而生成更准确的SQL。

要求:
1. 只生成SELECT查询，不要生成INSERT、UPDATE、DELETE等修改数据的语句
2. SQL语句要符合标准SQL语法
3. 返回的SQL要能直接执行，不要包含任何解释文字
4. 只返回SQL语句本身，不要添加markdown代码块标记
5. 统计表中记录的数量（如 COUNT(*)）是有效的业务查询，应当支持。
6. 如果用户询问数据库结构（如“有多少张表”），请查询数据库系统的元数据表（如 sqlite_master, information_schema.tables 等）。
7. 对于同时要求“统计数量”和“列举明细”的问题，请尝试生成能一次性返回相关信息的查询（例如使用 GROUP BY 统计各分类数量，或者使用 LIMIT 限制明细数量）。
8. 严禁返回多条SQL语句。请始终将逻辑合并在一个SQL语句中返回，不要使用分号 (;) 分隔多个查询。
9. 如果问题确实无法转换为SQL（例如问题完全无关或涉及非法操作），返回: ERROR: [原因说明]

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
