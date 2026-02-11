import os
import logging
import logging.handlers
from datetime import datetime

def setup_logging(log_dir="logs"):
    """配置全局日志"""
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 日志格式
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 1. 基础应用日志 (app.log)
    app_log_path = os.path.join(log_dir, "app.log")
    app_handler = logging.handlers.RotatingFileHandler(
        app_log_path, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    app_handler.setFormatter(log_format)
    app_handler.setLevel(logging.INFO)

    # 2. 控制台日志
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    console_handler.setLevel(logging.INFO)

    # 配置根日志
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # 清除旧的 handler 防止重复
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
        
    root_logger.addHandler(app_handler)
    root_logger.addHandler(console_handler)

    # 3. 专门的 SQL/问答日志 (qa.log) 用于追溯分析
    qa_log_path = os.path.join(log_dir, "qa.log")
    qa_handler = logging.handlers.RotatingFileHandler(
        qa_log_path, maxBytes=5*1024*1024, backupCount=10, encoding='utf-8'
    )
    qa_handler.setFormatter(log_format)
    
    qa_logger = logging.getLogger("qa_logger")
    qa_logger.setLevel(logging.INFO)
    qa_logger.addHandler(qa_handler)
    qa_logger.propagate = False # 不传递给 root 以免在 app.log 中重复（如果需要合并则设为 True）

    logging.info(f"日志系统初始化完成，存储目录: {log_dir}")
    return qa_logger

def log_qa(question, sql, success, error_msg=None, user_context=None):
    """记录问答追踪日志，增加访客上下文"""
    qa_logger = logging.getLogger("qa_logger")
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "question": question,
        "sql": sql,
        "success": success,
        "error": error_msg,
        "context": user_context or {}
    }
    import json
    qa_logger.info(json.dumps(log_entry, ensure_ascii=False))
