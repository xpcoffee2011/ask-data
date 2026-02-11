"""Claude API交互模块"""

from anthropic import Anthropic
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ClaudeClient:
    """Claude API客户端"""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4096,
        temperature: float = 0,
    ):
        """
        初始化Claude客户端

        Args:
            api_key: Anthropic API密钥
            model: 使用的模型名称
            max_tokens: 最大token数
            temperature: 温度参数
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        生成回复

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词

        Returns:
            Claude的回复内容
        """
        try:
            logger.info(f"正在调用Claude API (模型: {self.model})")

            messages = [{"role": "user", "content": prompt}]

            kwargs = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "messages": messages,
            }

            if system_prompt:
                kwargs["system"] = system_prompt
                logger.debug(f"系统提示词: {system_prompt}")
            
            logger.info(f"发送用户提示词: \n{prompt}")
            response = self.client.messages.create(**kwargs)

            # 提取文本内容
            content = response.content[0].text
            logger.info(f"API调用成功，返回 {len(content)} 字符")
            logger.info(f"API回复内容: \n{content}")

            return content.strip()

        except Exception as e:
            logger.error(f"Claude API调用失败: {e}")
            raise RuntimeError(f"Claude API调用失败: {e}")

    def generate_stream(self, prompt: str, system_prompt: Optional[str] = None):
        """流式生成回复"""
        try:
            logger.info(f"正在启动 Claude 流式调用 (模型: {self.model})")

            messages = [{"role": "user", "content": prompt}]
            kwargs = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "messages": messages,
            }
            if system_prompt:
                kwargs["system"] = system_prompt

            with self.client.messages.stream(**kwargs) as stream:
                for text in stream.text_stream:
                    yield text

        except Exception as e:
            logger.error(f"Claude 流式内容失败: {e}")
            raise RuntimeError(f"Claude 流式内容失败: {e}")

    def generate_sql(self, question: str, schema: str, examples: str = "") -> str:
        """
        将自然语言问题转换为SQL

        Args:
            question: 自然语言问题
            schema: 数据库schema
            examples: 可选的示例

        Returns:
            生成的SQL语句
        """
        from .prompts import get_text_to_sql_prompt

        prompt = get_text_to_sql_prompt(question, schema, examples)
        sql = self.generate(prompt)

        # 清理SQL语句
        sql = sql.strip()
        # 移除可能的markdown代码块标记
        if sql.startswith("```sql"):
            sql = sql[6:]
        if sql.startswith("```"):
            sql = sql[3:]
        if sql.endswith("```"):
            sql = sql[:-3]
        sql = sql.strip()

        return sql

    def explain_results(self, question: str, sql: str, results: str) -> str:
        """
        解释查询结果

        Args:
            question: 原始问题
            sql: SQL语句
            results: 查询结果

        Returns:
            自然语言解释
        """
        from .prompts import get_result_explanation_prompt

        prompt = get_result_explanation_prompt(question, sql, results)
        explanation = self.generate(prompt)

        return explanation
