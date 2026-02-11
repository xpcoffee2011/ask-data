"""核心问数模块"""

from typing import Dict, Any, Optional
import logging

from ..database import DatabaseConnector, SchemaAnalyzer
from ..llm import ClaudeClient, QwenClient
from ..sql import SQLValidator, SQLExecutor
from ..utils.logger import log_qa

logger = logging.getLogger(__name__)


class AskData:
    """智能问数核心类"""

    def __init__(
        self,
        database_url: str,
        llm_provider: str = "claude",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0,
        allow_only_select: bool = True,
        max_results: int = 1000,
    ):
        """
        初始化智能问数系统

        Args:
            database_url: 数据库连接URL
            llm_provider: LLM提供商 ('claude' 或 'qwen')
            api_key: API密钥
            model: 模型名称
            base_url: API基础URL (针对Qwen等)
            max_tokens: 最大token数
            temperature: 温度参数
            allow_only_select: 是否只允许SELECT查询
            max_results: 最大返回结果数
        """
        # 初始化数据库
        self.db_connector = DatabaseConnector(database_url)
        self.schema_analyzer = SchemaAnalyzer(self.db_connector.engine)

        # 初始化LLM
        if llm_provider == "qwen":
            self.llm = QwenClient(
                api_key=api_key,
                model=model,
                base_url=base_url,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        else:
            self.llm = ClaudeClient(
                api_key=api_key,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
            )

        # 初始化SQL处理
        self.validator = SQLValidator(allow_only_select=allow_only_select)
        self.executor = SQLExecutor(
            self.db_connector.engine, max_results=max_results
        )

        # 缓存schema描述
        self._schema_description: Optional[str] = None

        logger.info(f"智能问数系统初始化完成 (提供商: {llm_provider},模型:{model})")

    @property
    def schema_description(self) -> str:
        """获取数据库schema描述（带缓存）"""
        if self._schema_description is None:
            self._schema_description = self.schema_analyzer.generate_schema_description()
        return self._schema_description

    def refresh_schema(self):
        """刷新schema缓存"""
        self._schema_description = None
        logger.info("Schema缓存已刷新")

    def ask(
        self, question: str, explain_results: bool = True, user_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        用自然语言查询数据库

        Returns:
            包含SQL、结果和解释的字典
        """
        result = {
            "question": question,
            "sql": None,
            "data": None,
            "columns": None,
            "formatted_results": None,
            "explanation": None,
            "error": None,
        }

        try:
            logger.info("="*75)
            logger.info("="*75)
            # 1. 生成SQL
            logger.info(f"处理问题: {question}")
            from ..llm.prompts import EXAMPLES
            sql = self.llm.generate_sql(question, self.schema_description, EXAMPLES)
            result["sql"] = sql

            # 2. 验证SQL
            is_valid, message = self.validator.validate(sql)
            if not is_valid:
                result["error"] = message
                return result

            # 清理SQL
            sql = self.validator.sanitize(sql)
            result["sql"] = sql

            # 3. 执行SQL
            data, columns = self.executor.execute(sql)
            result["data"] = data
            result["columns"] = columns
            result["formatted_results"] = self.executor.format_results(
                data, columns
            )

            # 4. 解释结果
            if explain_results and data:
                result["explanation"] = self.llm.explain_results(
                    question, sql, result["formatted_results"]
                )
            
            # 记录成功日志
            log_qa(question, sql, True, user_context=user_context)

        except Exception as e:
            logger.error(f"查询失败: {e}")
            result["error"] = str(e)
            # 记录失败日志
            log_qa(question, result.get("sql"), False, str(e), user_context=user_context)

        return result

    def ask_stream(self, question: str, user_context: Optional[Dict] = None):
        """
        流式查询数据库
        支持逐步返回: SQL -> 数据 -> 解释内容
        """
        try:
            from ..llm.prompts import EXAMPLES, get_result_explanation_prompt

            # 1. 生成 SQL
            logger.info(f"正在为问题生成 SQL: {question}")
            sql = self.llm.generate_sql(question, self.schema_description, EXAMPLES)
            
            # 验证并清理 SQL
            is_valid, message = self.validator.validate(sql)
            if not is_valid:
                yield {"type": "error", "content": message}
                return

            sql = self.validator.sanitize(sql)
            yield {"type": "sql", "content": sql}

            # 2. 执行 SQL
            logger.info(f"正在执行 SQL 并获取数据")
            data, columns = self.executor.execute(sql)
            formatted_results = self.executor.format_results(data, columns)
            
            yield {
                "type": "data", 
                "content": {
                    "data": data,
                    "columns": columns,
                    "formatted_results": formatted_results
                }
            }

            # 3. 流式解释结果
            if data:
                logger.info(f"正在流式生成结果解释")
                prompt = get_result_explanation_prompt(question, sql, formatted_results)
                
                # 开始发送解释内容前的信号
                yield {"type": "explanation_start", "content": ""}
                
                for chunk in self.llm.generate_stream(prompt):
                    yield {"type": "explanation_chunk", "content": chunk}
                
                yield {"type": "explanation_end", "content": ""}
            
            # 记录成功流式日志
            log_qa(question, sql, True, user_context=user_context)

        except Exception as e:
            logger.error(f"流式查询失败: {e}")
            yield {"type": "error", "content": str(e)}
            # 记录失败流式日志
            log_qa(question, locals().get("sql"), False, str(e), user_context=user_context)


    def get_tables(self) -> list:
        """获取数据库中的所有表"""
        return self.schema_analyzer.get_all_tables()

    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """获取指定表的详细信息"""
        return self.schema_analyzer.get_table_schema(table_name)

    def close(self):
        """关闭连接"""
        self.db_connector.close()
