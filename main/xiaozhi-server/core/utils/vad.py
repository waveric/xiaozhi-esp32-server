import importlib
import os
import sys
from core.providers.vad.base import VADProviderBase
from config.logger import setup_logging

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
sys.path.insert(0, project_root)

TAG = __name__
logger = setup_logging()


def create_instance(class_name: str, *args, **kwargs) -> VADProviderBase:
    """工厂方法创建VAD实例"""
    provider_path = os.path.join(project_root, "core", "providers", "vad", f"{class_name}.py")
    if os.path.exists(provider_path):
        lib_name = f"core.providers.vad.{class_name}"
        if lib_name not in sys.modules:
            sys.modules[lib_name] = importlib.import_module(f"{lib_name}")
        return sys.modules[lib_name].VADProvider(*args, **kwargs)

    raise ValueError(f"不支持的VAD类型: {class_name}，请检查该配置的type是否设置正确。查找路径: {provider_path}")
