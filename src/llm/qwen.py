"""Qwen API交互模块 (OpenAI兼容接口)"""

from openai import OpenAI
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class QwenClient:
    """通义千问 API客户端"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        model: str = "qwen-plus",
        max_tokens: int = 4096,
        temperature: float = 0,
    ):
        """
        初始化Qwen客户端

        Args:
            api_key: DashScope API密钥
            base_url: API基础URL
            model: 使用的模型名称
            max_tokens: 最大token数
            temperature: 温度参数
        """
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """生成回复"""
        try:
            logger.info(f"正在调用 Qwen API (模型: {self.model})")

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            content = response.choices[0].message.content
            return content.strip()

        except Exception as e:
            logger.error(f"Qwen API调用失败: {e}")
            raise RuntimeError(f"Qwen API调用失败: {e}")

    def generate_stream(self, prompt: str, system_prompt: Optional[str] = None):
        """流式生成回复"""
        try:
            logger.info(f"正在启动 Qwen 流式调用 (模型: {self.model})")

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=True,
            )

            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Qwen 流式调用失败: {e}")
            raise RuntimeError(f"Qwen 流式调用失败: {e}")

    def generate_sql(self, question: str, schema: str, examples: str = "") -> str:
        """将自然语言问题转换为SQL"""
        from .prompts import get_text_to_sql_prompt

        prompt = get_text_to_sql_prompt(question, schema, examples)
        sql = self.generate(prompt)

        # 清理SQL语句
        sql = sql.strip()
        if sql.startswith("```sql"):
            sql = sql[6:]
        if sql.startswith("```"):
            sql = sql[3:]
        if sql.endswith("```"):
            sql = sql[:-3]
        sql = sql.strip()

        return sql

    def explain_results(self, question: str, sql: str, results: str) -> str:
        """解释查询结果"""
        from .prompts import get_result_explanation_prompt

        prompt = get_result_explanation_prompt(question, sql, results)
        explanation = self.generate(prompt)

        return explanation
