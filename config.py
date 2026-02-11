import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """配置管理类"""

    # LLM 选择: 'claude' 或 'qwen'
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "claude").lower()

    # Claude API配置
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")

    # Qwen API配置
    QWEN_API_KEY = os.getenv("QWEN_API_KEY")
    QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen-plus")
    QWEN_BASE_URL = os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")

    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0"))

    # 数据库配置
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///example.db")

    # 安全配置
    ALLOW_ONLY_SELECT = True  # 仅允许SELECT查询
    MAX_RESULTS = 1000  # 最大返回结果数

    @classmethod
    def validate(cls):
        """验证必要的配置是否存在"""
        if cls.LLM_PROVIDER == "claude" and not cls.ANTHROPIC_API_KEY:
            raise ValueError("LLM_PROVIDER 为 claude 但 ANTHROPIC_API_KEY 未设置")
        if cls.LLM_PROVIDER == "qwen" and not cls.QWEN_API_KEY:
            raise ValueError("LLM_PROVIDER 为 qwen 但 QWEN_API_KEY 未设置")
        
        if not cls.DATABASE_URL:
            raise ValueError("DATABASE_URL未设置，请在.env文件中配置")
        return True


# 验证配置
if __name__ == "__main__":
    try:
        Config.validate()
        print("✓ 配置验证通过")
        print(f"  - Claude模型: {Config.CLAUDE_MODEL}")
        print(f"  - 数据库: {Config.DATABASE_URL}")
    except ValueError as e:
        print(f"✗ 配置错误: {e}")
