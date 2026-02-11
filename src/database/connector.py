"""数据库连接模块"""

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DatabaseConnector:
    """数据库连接器"""

    def __init__(self, database_url: str):
        """
        初始化数据库连接

        Args:
            database_url: 数据库连接URL
        """
        self.database_url = database_url
        self._engine: Optional[Engine] = None

    def connect(self) -> Engine:
        """建立数据库连接"""
        if self._engine is None:
            try:
                self._engine = create_engine(self.database_url)
                # 测试连接
                with self._engine.connect() as conn:
                    logger.info(f"数据库连接成功: {self.database_url.split(':/')[0]}")
                return self._engine
            except Exception as e:
                logger.error(f"数据库连接失败: {e}")
                raise ConnectionError(f"无法连接到数据库: {e}")
        return self._engine

    @property
    def engine(self) -> Engine:
        """获取数据库引擎"""
        if self._engine is None:
            return self.connect()
        return self._engine

    def get_inspector(self):
        """获取数据库检查器"""
        return inspect(self.engine)

    def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            with self.engine.connect() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"数据库连接测试失败: {e}")
            return False

    def close(self):
        """关闭数据库连接"""
        if self._engine:
            self._engine.dispose()
            self._engine = None
            logger.info("数据库连接已关闭")
