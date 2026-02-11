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

        # 检查分号注入（多条语句）
        statements = [s.strip() for s in sql.split(";") if s.strip()]
        if len(statements) > 1:
            return False, "不允许执行多条SQL语句"

        logger.info(f"SQL验证通过: {sql[:50]}...")
        return True, "验证通过"

    def sanitize(self, sql: str) -> str:
        """
        清理SQL语句

        Args:
            sql: 原始SQL语句

        Returns:
            清理后的SQL语句
        """
        # 移除多余的空白字符
        sql = " ".join(sql.split())

        # 移除末尾的分号
        sql = sql.rstrip(";")

        return sql.strip()
