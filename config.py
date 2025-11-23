from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from pathlib import Path

class CharacterConfig(BaseModel):
    """角色配置"""
    name: str
    birthday: str  # 格式: "MM-DD"
    image_file: str

class PluginConfig(BaseModel):
    """插件配置"""
    # 是否启用群聊推送
    enable_group: bool = True
    # 白名单群组
    white_list_groups: List[int] = []

class PjskBirthdayConfig(BaseModel):
    """总配置"""
    plugin_config: PluginConfig
    characters: Dict[str, Dict[str, Any]]  # 修改为接受任意嵌套结构