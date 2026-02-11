#!/usr/bin/env python3
"""
智能问数 - 主程序入口
基于 AI 的数据库自然语言查询系统
"""

import os
import sys
import logging
from prompt_toolkit import PromptSession
from config import Config
from src.core import AskData

# 配置双重日志 (控制台 + 文件)
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "ask_data.log")

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 设置根日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),  # 打印到控制台
        logging.FileHandler(LOG_FILE, encoding='utf-8')  # 打印到文件
    ]
)
logger = logging.getLogger(__name__)


def print_result(result: dict):
    """打印查询结果"""
    print("\n" + "=" * 60)

    if result.get("error"):
        print(f"错误: {result['error']}")
        return

    print(f"问题: {result['question']}")
    print(f"\n生成的SQL:\n{result['sql']}")

    if result.get("formatted_results"):
        print(f"\n查询结果（展示给用户）:\n{result['formatted_results']}")

    if result.get("explanation"):
        print(f"\n结果解释（大模型思考过程）:\n{result['explanation']}")

    print("=" * 60)


def interactive_mode(asker: AskData):
    """交互式查询模式"""
    session = PromptSession()
    print("\n智能问数系统已启动")
    print("输入自然语言问题来查询数据库")
    print("输入 'tables' 查看所有表")
    print("输入 'schema' 查看数据库结构")
    print("输入 'quit' 或 'exit' 退出\n")

    while True:
        try:
            question = session.prompt("请输入问题: ").strip()

            if not question:
                continue

            if question.lower() in ("quit", "exit", "q"):
                print("再见!")
                break

            if question.lower() == "tables":
                tables = asker.get_tables()
                print(f"\n数据库中的表: {', '.join(tables)}\n")
                continue

            if question.lower() == "schema":
                print(f"\n{asker.schema_description}\n")
                continue

            # 执行查询
            result = asker.ask(question)
            print_result(result)

        except KeyboardInterrupt:
            print("\n再见!")
            break
        except EOFError:
            break
        except Exception as e:
            print(f"发生错误: {e}")


def main():
    """主函数"""
    try:
        # 验证配置
        Config.validate()
    except ValueError as e:
        print(f"配置错误: {e}")
        print("请检查 .env 文件并填入必要的配置")
        sys.exit(1)

    # 准备 LLM 配置
    llm_params = {
        "llm_provider": Config.LLM_PROVIDER,
        "max_tokens": Config.MAX_TOKENS,
        "temperature": Config.TEMPERATURE,
    }

    if Config.LLM_PROVIDER == "qwen":
        llm_params.update({
            "api_key": Config.QWEN_API_KEY,
            "model": Config.QWEN_MODEL,
            "base_url": Config.QWEN_BASE_URL,
        })
    else:
        llm_params.update({
            "api_key": Config.ANTHROPIC_API_KEY,
            "model": Config.CLAUDE_MODEL,
        })

    # 初始化系统
    print(f"正在初始化智能问数系统 (使用模型: {Config.LLM_PROVIDER})...")
    try:
        asker = AskData(
            database_url=Config.DATABASE_URL,
            allow_only_select=Config.ALLOW_ONLY_SELECT,
            max_results=Config.MAX_RESULTS,
            **llm_params
        )
    except Exception as e:
        print(f"初始化失败: {e}")
        sys.exit(1)

    # 进入交互模式
    try:
        interactive_mode(asker)
    finally:
        asker.close()


if __name__ == "__main__":
    main()
