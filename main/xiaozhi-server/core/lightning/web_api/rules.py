"""
行为规则 API（xiaozhi-esp32-server 集成版）
读写 agent-base-prompt.txt
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..config import AGENT_BASE_PROMPT_PATH

router = APIRouter(prefix="/admin/api", tags=["rules"])


class RulesUpdate(BaseModel):
    content: str


# ===== Rules API =====

@router.get("/rules")
async def api_get_rules():
    """获取行为规则内容"""
    try:
        with open(AGENT_BASE_PROMPT_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        return {"content": content}
    except FileNotFoundError:
        return {"content": "", "error": "Rules file not found"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read rules: {str(e)}")


@router.put("/rules")
async def api_set_rules(data: RulesUpdate):
    """更新行为规则内容"""
    try:
        with open(AGENT_BASE_PROMPT_PATH, "w", encoding="utf-8") as f:
            f.write(data.content)
        return {"success": True, "content": data.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write rules: {str(e)}")
