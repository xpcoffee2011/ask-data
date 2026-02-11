import os
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date
from decimal import Decimal
import json

from config import Config
from src.core import AskData
from src.utils.logger import setup_logging
from contextlib import asynccontextmanager

from fastapi.responses import JSONResponse

# 自定义 JSON 处理器处理 Decimal 等类型
def json_serial(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

class CustomJSONResponse(JSONResponse):
    def render(self, content: Any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
            default=json_serial,
        ).encode("utf-8")

# 实例化 AskData
asker = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时：初始化日志和 Asker
    setup_logging()
    get_asker()
    yield
    # 关闭时：清理资源
    if asker:
        asker.close()

# 初始化 FastAPI
app = FastAPI(
    title="智能问数 API", 
    description="基于 AI 的数据库自然语言查询接口",
    default_response_class=CustomJSONResponse,
    lifespan=lifespan
)

def get_asker(overrides: Optional[dict] = None):
    global asker
    if asker is None or overrides:
        Config.validate()
        
        # 基础配置
        safe_overrides = overrides or {}
        base_model = safe_overrides.get("model")
        
        # 智能判定 Provider
        # 如果模型名包含 claude，则强制使用 anthropic 提供商
        if base_model and "claude" in base_model.lower():
            provider = "anthropic"
        elif not base_model:
            provider = Config.LLM_PROVIDER
        else:
            provider = "qwen"

        llm_params = {
            "llm_provider": provider,
            "max_tokens": int(safe_overrides.get("max_tokens", Config.MAX_TOKENS)),
            "temperature": float(safe_overrides.get("temperature", Config.TEMPERATURE)),
            "model": base_model
        }

        if provider == "qwen":
            llm_params.update({
                "api_key": Config.QWEN_API_KEY,
                "base_url": Config.QWEN_BASE_URL,
            })
            if not llm_params["model"]:
                llm_params["model"] = Config.QWEN_MODEL
        else:
            llm_params.update({
                "api_key": Config.ANTHROPIC_API_KEY,
            })
            if not llm_params["model"]:
                llm_params["model"] = Config.CLAUDE_MODEL
        
        current_asker = AskData(
            database_url=Config.DATABASE_URL,
            allow_only_select=Config.ALLOW_ONLY_SELECT,
            max_results=Config.MAX_RESULTS,
            **llm_params
        )
        if not overrides:
            asker = current_asker
        return current_asker
    return asker

class QuestionRequest(BaseModel):
    question: str
    config: Optional[dict] = None

from fastapi.responses import FileResponse, StreamingResponse

@app.post("/api/ask")
async def ask_question(request_body: QuestionRequest, request: Request):
    async def event_generator():
        try:
            # 提取访客信息
            user_context = {
                "ip": request.client.host,
                "user_agent": request.headers.get("user-agent"),
                "forwarded_for": request.headers.get("x-forwarded-for"),
                "referer": request.headers.get("referer")
            }
            
            a = get_asker(overrides=request_body.config)
            for event in a.ask_stream(request_body.question, user_context=user_context):
                # 按照 SSE 格式发送数据
                yield f"data: {json.dumps(event, default=json_serial, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/api/examples")
async def get_examples():
    return [
        {"title": "数据库概况", "question": "数据库里有多少张表？"},
        {"title": "用户统计", "question": "显示系统里所有用户的数量"},
        {"title": "销售分析", "question": "找出销售额最高的5个产品"},
        {"title": "分类价格", "question": "计算每个分类的平均价格"}
    ]

@app.get("/api/full_schema")
async def get_full_schema():
    try:
        a = get_asker()
        return a.schema_analyzer.get_database_schema()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/db_info")
async def get_db_info():
    try:
        a = get_asker()
        return {
            "tables": a.get_tables(),
            "schema_description": a.schema_description
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 挂载静态文件
if not os.path.exists("static"):
    os.makedirs("static")

app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
