"""SQL执行模块"""

from sqlalchemy import text
from sqlalchemy.engine import Engine
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class SQLExecutor:
    """SQL执行器"""

    def __init__(self, engine: Engine, max_results: int = 1000):
        """
        初始化SQL执行器

        Args:
            engine: SQLAlchemy数据库引擎
            max_results: 最大返回结果数
        """
        self.engine = engine
        self.max_results = max_results

    def execute(self, sql: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        执行SQL查询

        Args:
            sql: SQL查询语句

        Returns:
            (查询结果列表, 列名列表)
        """
        try:
            logger.info(f"执行SQL: {sql}")

            with self.engine.connect() as conn:
                result = conn.execute(text(sql))
                columns = list(result.keys())
                rows = result.fetchmany(self.max_results)

                # 转换为字典列表
                data = [dict(zip(columns, row)) for row in rows]

                logger.info(f"查询成功，返回 {len(data)} 行")
                return data, columns

        except Exception as e:
            logger.error(f"SQL执行失败: {e}")
            raise RuntimeError(f"SQL执行失败: {e}")

    def format_results(
        self, data: List[Dict[str, Any]], columns: List[str], max_display: int = 20
    ) -> str:
        """
        格式化查询结果为表格字符串

        Args:
            data: 查询结果
            columns: 列名
            max_display: 最大显示行数

        Returns:
            格式化的表格字符串
        """
        if not data:
            return "（无数据）"

        # 计算每列的最大宽度
        widths = {col: len(str(col)) for col in columns}
        for row in data[:max_display]:
            for col in columns:
                val = str(row.get(col, ""))
                widths[col] = max(widths[col], min(len(val), 50))

        # 生成表头
        header = " | ".join(str(col).ljust(widths[col]) for col in columns)
        separator = "-+-".join("-" * widths[col] for col in columns)

        # 生成数据行
        lines = [header, separator]
        for i, row in enumerate(data):
            if i >= max_display:
                lines.append(f"... 还有 {len(data) - max_display} 行未显示")
                break
            line = " | ".join(
                str(row.get(col, ""))[:50].ljust(widths[col]) for col in columns
            )
            lines.append(line)

        return "\n".join(lines)
