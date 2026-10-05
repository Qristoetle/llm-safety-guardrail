# -*- coding: utf-8 -*-
"""
日志路由
"""

import os
import re
import json
import time
import logging

from fastapi import APIRouter, HTTPException

from ..models import SnapshotRequest
from ..config import config
from ..utils.logs import execution_logs_history, save_logs_to_file

router = APIRouter()
logger = logging.getLogger("ai_security")

SNAPSHOT_DIR = config.SNAPSHOT_DIR
os.makedirs(SNAPSHOT_DIR, exist_ok=True)


def _sanitize_filename(name: str) -> str:
    """清理文件名"""
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.replace("..", "").replace("/", "").replace("\\", "")
    sanitized = name.strip() or f"snapshot_{int(time.time())}"
    return f"{sanitized}.json"


@router.get("/logs/history")
async def get_logs_history(limit: int = 50):
    """获取历史执行日志"""
    try:
        return {
            "success": True,
            "total": len(execution_logs_history),
            "logs": execution_logs_history[-limit:][::-1]
        }
    except Exception as e:
        logger.error(f"获取历史日志时出错: {e}")
        return {"success": False, "error": str(e)}


@router.delete("/logs/history")
async def clear_logs_history():
    """清空历史执行日志"""
    try:
        global execution_logs_history
        execution_logs_history.clear()
        save_logs_to_file()
        return {"success": True, "message": "历史日志已清空"}
    except Exception as e:
        logger.error(f"清空历史日志时出错: {e}")
        return {"success": False, "error": str(e)}


@router.get("/logs/snapshots")
async def get_snapshots_list():
    """获取所有已保存快照的详细信息列表"""
    snapshots_metadata = []
    if not os.path.exists(SNAPSHOT_DIR):
        return {"success": True, "snapshots": []}
    
    try:
        for filename in os.listdir(SNAPSHOT_DIR):
            if filename.endswith(".json"):
                filepath = os.path.join(SNAPSHOT_DIR, filename)
                try:
                    mtime = os.path.getmtime(filepath)
                    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime))
                    
                    with open(filepath, "r", encoding="utf-8") as f:
                        logs = json.load(f)
                        total = len(logs) if isinstance(logs, list) else 0
                    
                    snapshots_metadata.append({
                        "filename": filename,
                        "name": filename.replace(".json", ""),
                        "timestamp": timestamp,
                        "total": total
                    })
                except Exception:
                    continue
        
        snapshots_metadata.sort(key=lambda x: x['timestamp'], reverse=True)
        return {"success": True, "snapshots": snapshots_metadata}
    
    except Exception as e:
        logger.error(f"读取快照列表失败: {e}")
        raise HTTPException(status_code=500, detail="无法读取快照列表")


@router.get("/logs/snapshot/{filename}")
async def get_snapshot_content(filename: str):
    """根据文件名获取特定快照的日志内容"""
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="无效的文件名")
    
    filepath = os.path.join(SNAPSHOT_DIR, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="指定的快照不存在")
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            logs = json.load(f)
        
        mtime = os.path.getmtime(filepath)
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime))
        
        response_data = {
            "name": filename.replace(".json", ""),
            "timestamp": timestamp,
            "total": len(logs) if isinstance(logs, list) else 0,
            "logs": logs
        }
        return {"success": True, "data": response_data}
    
    except Exception as e:
        logger.error(f"读取快照 '{filename}' 失败: {e}")
        raise HTTPException(status_code=500, detail="无法读取快照文件")


@router.post("/logs/save")
async def create_snapshot(request: SnapshotRequest):
    """将当前内存中的日志保存为一个命名的快照"""
    filename = _sanitize_filename(request.name)
    filepath = os.path.join(SNAPSHOT_DIR, filename)
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(execution_logs_history, f, ensure_ascii=False, indent=2)
        
        clean_name = filename.replace(".json", "")
        logger.info(f"成功将 {len(execution_logs_history)} 条日志保存为快照: '{clean_name}'")
        return {
            "success": True,
            "message": f"快照 '{clean_name}' 已成功保存。",
            "snapshot_name": clean_name
        }
    except Exception as e:
        logger.error(f"保存快照 '{request.name}' 失败: {e}")
        raise HTTPException(status_code=500, detail=f"保存快照时发生错误: {e}")
