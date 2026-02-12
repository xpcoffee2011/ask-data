"""数据库Schema分析模块"""

from sqlalchemy import inspect, MetaData, Table, text
from sqlalchemy.engine import Engine
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class SchemaAnalyzer:
    """数据库Schema分析器"""

    def __init__(self, engine: Engine):
        """
        初始化Schema分析器

        Args:
            engine: SQLAlchemy数据库引擎
        """
        self.engine = engine
        self.inspector = inspect(engine)
        self.metadata = MetaData()

    def get_all_tables(self) -> List[str]:
        """获取所有表名"""
        return self.inspector.get_table_names()

    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """
        获取指定表的详细schema

        Args:
            table_name: 表名

        Returns:
            包含表结构信息的字典
        """
        columns = self.inspector.get_columns(table_name)
        # 将 SQLAlchemy 类型对象转换为字符串，方便 JSON 序列化和前端展示
        for col in columns:
            col['type'] = str(col['type'])
            
        primary_keys = self.inspector.get_pk_constraint(table_name)
        foreign_keys = self.inspector.get_foreign_keys(table_name)
        indexes = self.inspector.get_indexes(table_name)

        return {
            "table_name": table_name,
            "columns": columns,
            "primary_keys": primary_keys,
            "foreign_keys": foreign_keys,
            "indexes": indexes,
            "sample_data": self.get_sample_data(table_name, limit=5)
        }

    def get_database_schema(self) -> Dict[str, Any]:
        """
        获取整个数据库的schema

        Returns:
            包含所有表结构信息的字典
        """
        tables = self.get_all_tables()
        schema = {"tables": {}}

        for table_name in tables:
            try:
                schema["tables"][table_name] = self.get_table_schema(table_name)
                logger.info(f"已分析表: {table_name}")
            except Exception as e:
                logger.error(f"分析表 {table_name} 失败: {e}")

        return schema

    def generate_schema_description(self) -> str:
        """
        生成人类可读的数据库schema描述

        Returns:
            格式化的schema描述字符串
        """
        schema = self.get_database_schema()
        dialect = self.engine.name
        tables = list(schema["tables"].keys())
        
        description_parts = [
            "数据库概况:",
            f"  - 数据库类型: {dialect}",
            f"  - 总表数: {len(tables)}",
            f"  - 所有表: {', '.join(tables)}",
            "\n详细结构:"
        ]

        for table_name, table_info in schema["tables"].items():
            description_parts.append(f"\n表: {table_name}")

            # 列信息
            description_parts.append("  列:")
            for col in table_info["columns"]:
                col_desc = f"    - {col['name']}: {col['type']}"
                if col.get("nullable") is False:
                    col_desc += " (NOT NULL)"
                if col.get("default"):
                    col_desc += f" DEFAULT {col['default']}"
                description_parts.append(col_desc)

            # 主键
            if table_info["primary_keys"]["constrained_columns"]:
                pk_cols = ", ".join(table_info["primary_keys"]["constrained_columns"])
                description_parts.append(f"  主键: {pk_cols}")

            # 外键
            if table_info["foreign_keys"]:
                description_parts.append("  外键:")
                for fk in table_info["foreign_keys"]:
                    fk_desc = f"    - {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}"
                    description_parts.append(fk_desc)

            # 示例数据
            sample_data = self.get_sample_data(table_name, limit=3)
            if sample_data:
                description_parts.append("  示例数据 (前3行):")
                for i, row in enumerate(sample_data):
                    description_parts.append(f"    行 {i+1}: {row}")

        return "\n".join(description_parts)

    def get_sample_data(self, table_name: str, limit: int = 3) -> List[Dict]:
        """
        获取表的示例数据

        Args:
            table_name: 表名
            limit: 返回的行数

        Returns:
            示例数据列表
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT {limit}"))
                columns = result.keys()
                return [dict(zip(columns, row)) for row in result.fetchall()]
        except Exception as e:
            logger.error(f"获取表 {table_name} 示例数据失败: {e}")
            return []
