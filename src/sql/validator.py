"""SQL验证模块"""

import re
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

# 危险的SQL关键字（可能修改数据）
DANGEROUS_KEYWORDS = [
    r"\bINSERT\b",
    r"\bUPDATE\b",
    r"\bDELETE\b",
    r"\bDROP\b",
    r"\bTRUNCATE\b",
    r"\bALTER\b",
    r"\bCREATE\b",
    r"\bGRANT\b",
    r"\bREVOKE\b",
    r"\bEXEC\b",
    r"\bEXECUTE\b",
]


class SQLValidator:
    """SQL验证器"""

    def __init__(self, allow_only_select: bool = True):
        """
        初始化SQL验证器

        Args:
            allow_only_select: 是否只允许SELECT语句
        """
        self.allow_only_select = allow_only_select

    def validate(self, sql: str) -> Tuple[bool, str]:
        """
        验证SQL语句的安全性

        Args:
            sql: 待验证的SQL语句

        Returns:
            (是否通过验证, 验证消息)
        """
        # 先执行基本的清理（如移除末尾分号）
        sql = self.sanitize(sql)
        sql_upper = sql.upper().strip()

        # 检查是否为空
        if not sql:
            return False, "SQL语句不能为空"

        # 检查是否以ERROR开头（LLM返回的错误）
        if sql_upper.startswith("ERROR"):
            return False, sql

        # 如果只允许SELECT，检查是否为SELECT语句
        if self.allow_only_select:
            if not sql_upper.startswith("SELECT"):
                return False, "只允许执行SELECT查询"

        # 检查危险关键字
        for keyword in DANGEROUS_KEYWORDS:
            if re.search(keyword, sql_upper):
                return False, f"SQL包含不允许的操作: {keyword}"

        # 移除严格的多语句检查，仅保留基本的消毒处理
        # 此时 sql 已经经过 sanitize 处理，末尾的分号应该已经被移除
        # 如果用户输入了 'SELECT 1; SELECT 2;'，sanitize 会将其变为 'SELECT 1; SELECT 2'
        # 但因为我们不再检查分号数量，所以这种多语句仍然会通过
        # 如果需要严格限制单条语句，则需要重新引入多语句检查
        
        logger.info(f"SQL验证通过: {sql[:50]}...")
        return True, "验证通过"

    def sanitize(self, sql: str) -> str:
        """
        清理SQL语句，移除 Markdown 标记和冗余解释
        """
        # 1. 移除 Markdown 代码块标记
        sql = re.sub(r"```sql\s*", "", sql, flags=re.IGNORECASE)
        sql = re.sub(r"```\s*", "", sql, flags=re.IGNORECASE)

        # 2. 如果 SQL 中间有分号，且分号后面跟着中文或备注类文字，则截断
        # 匹配分号后紧跟常见的 AI 废话开头
        pats = [r";\s*注意", r";\s*备注", r";\s*说明", r";\s*NOTE", r";\s*REMINDER"]
        for pat in pats:
            parts = re.split(pat, sql, flags=re.IGNORECASE)
            if len(parts) > 1:
                sql = parts[0]
                break

        # 3. 移除多余的空白字符
        sql = " ".join(sql.split())

        # 4. 移除末尾可能残留的分号
        sql = sql.rstrip(";")

        return sql.strip()
