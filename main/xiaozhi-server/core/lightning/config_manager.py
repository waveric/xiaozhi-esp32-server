"""
ConfigManager - 配置文件管理核心类

管理 xiaozhi-esp32-server 的配置文件:
- 默认配置 (config.yaml) 只读
- 支持读取/保存/切换配置文件
- 配置文件存储在 data/configs/ 目录
"""

import yaml
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any


class ConfigManager:
    """配置文件管理器

    默认配置文件 (config.yaml) 是只读的，作为系统默认值。
    用户可以通过激活配置 (.config.yaml) 覆盖默认配置。
    其他配置文件保存在 data/configs/ 目录下。
    """

    DEFAULT_CONFIG = "config.yaml"  # 默认配置，只读

    def __init__(self, base_dir: Optional[Path] = None):
        """初始化配置管理器

        Args:
            base_dir: 项目根目录，默认为 main/xiaozhi-server
        """
        self.base_dir = base_dir or Path(__file__).parent.parent.parent
        self.configs_dir = self.base_dir / "data" / "configs"
        self.active_config = self.base_dir / "data" / ".config.yaml"
        self.default_config_path = self.base_dir / self.DEFAULT_CONFIG

        # 确保 configs 目录存在
        self.configs_dir.mkdir(parents=True, exist_ok=True)

    def get_default_config(self) -> Dict[str, Any]:
        """读取只读默认配置

        Returns:
            默认配置字典

        Raises:
            FileNotFoundError: 默认配置文件不存在
        """
        if not self.default_config_path.exists():
            raise FileNotFoundError(f"默认配置文件不存在: {self.default_config_path}")

        with open(self.default_config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}

    def get_active_config(self) -> Dict[str, Any]:
        """读取当前激活的配置

        如果激活配置不存在，返回默认配置。

        Returns:
            当前配置字典
        """
        if self.active_config.exists():
            with open(self.active_config, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return self.get_default_config()

    def get_merged_config(self) -> Dict[str, Any]:
        """获取合并后的配置（默认 + 激活配置）

        激活配置会覆盖默认配置中的相同键。

        Returns:
            合并后的配置字典
        """
        default = self.get_default_config()
        active = self.get_active_config() if self.active_config.exists() else {}

        def deep_merge(base: Dict, override: Dict) -> Dict:
            """深度合并两个字典"""
            result = base.copy()
            for key, value in override.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result

        return deep_merge(default, active)

    def save_config(self, filename: str, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """保存配置到 data/configs/ 下指定文件

        Args:
            filename: 配置文件名（如 "production.yaml"）
            config_dict: 配置字典

        Returns:
            包含保存结果的字典
        """
        # 确保文件名以 .yaml 结尾
        if not filename.endswith('.yaml') and not filename.endswith('.yml'):
            filename = f"{filename}.yaml"

        target_path = self.configs_dir / filename

        try:
            with open(target_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

            return {
                "success": True,
                "path": str(target_path),
                "filename": filename
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def load_config(self, filename: str) -> Dict[str, Any]:
        """从 data/configs/ 加载指定配置文件

        Args:
            filename: 配置文件名

        Returns:
            配置字典

        Raises:
            FileNotFoundError: 配置文件不存在
        """
        # 自动补全文件名
        if not filename.endswith('.yaml') and not filename.endswith('.yml'):
            filename = f"{filename}.yaml"

        config_path = self.configs_dir / filename

        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}

    def list_configs(self) -> List[Dict[str, Any]]:
        """列出所有可用配置文件及激活状态

        Returns:
            配置文件列表，每个元素包含 name, path, is_active
        """
        configs = []

        # 遍历 configs 目录下的所有 yaml 文件
        for f in self.configs_dir.glob("*.yaml"):
            config_info = {
                "name": f.name,
                "path": str(f),
                "is_active": False,
                "modified": f.stat().st_mtime if f.exists() else None
            }
            configs.append(config_info)

        # 也添加 .yml 文件
        for f in self.configs_dir.glob("*.yml"):
            config_info = {
                "name": f.name,
                "path": str(f),
                "is_active": False,
                "modified": f.stat().st_mtime if f.exists() else None
            }
            configs.append(config_info)

        # 标记激活的配置
        if self.active_config.exists():
            try:
                active_content = self.active_config.read_text(encoding='utf-8')
                active_config = yaml.safe_load(active_content) or {}

                # 通过比较配置内容或特定标识来确定激活配置
                # 这里简化处理：检查配置文件的名称属性或唯一标识
                for cfg in configs:
                    try:
                        cfg_path = Path(cfg["path"])
                        cfg_content = cfg_path.read_text(encoding='utf-8')
                        if cfg_content.strip() == active_content.strip():
                            cfg["is_active"] = True
                            break
                    except Exception:
                        pass
            except Exception:
                pass

        # 按修改时间排序（最新的在前）
        configs.sort(key=lambda x: x.get("modified", 0) or 0, reverse=True)

        # 添加默认配置信息
        configs.insert(0, {
            "name": self.DEFAULT_CONFIG,
            "path": str(self.default_config_path),
            "is_active": not self.active_config.exists(),
            "modified": self.default_config_path.stat().st_mtime if self.default_config_path.exists() else None,
            "is_default": True
        })

        return configs

    def switch_config(self, filename: str) -> Dict[str, Any]:
        """切换配置文件

        将指定的配置文件复制为激活配置。
        需要重启服务才能生效。

        Args:
            filename: 要切换到的配置文件名

        Returns:
            包含切换结果的字典
        """
        # 自动补全文件名
        if not filename.endswith('.yaml') and not filename.endswith('.yml'):
            filename = f"{filename}.yaml"

        source = self.configs_dir / filename

        if not source.exists():
            return {
                "success": False,
                "error": f"配置文件 {filename} 不存在"
            }

        try:
            # 备份当前激活配置
            if self.active_config.exists():
                backup = self.active_config.with_suffix(".yaml.bak")
                shutil.copy(self.active_config, backup)

            # 复制目标配置为激活配置
            shutil.copy(source, self.active_config)

            return {
                "success": True,
                "requires_restart": True,
                "active_config": str(self.active_config),
                "source": str(source)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def reset_to_default(self) -> Dict[str, Any]:
        """重置为默认配置

        删除激活配置文件，系统将使用默认配置。

        Returns:
            包含重置结果的字典
        """
        try:
            if self.active_config.exists():
                # 备份当前配置
                backup = self.active_config.with_suffix(".yaml.bak")
                shutil.copy(self.active_config, backup)

                # 删除激活配置
                self.active_config.unlink()

            return {
                "success": True,
                "requires_restart": True,
                "message": "已重置为默认配置"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def delete_config(self, filename: str) -> Dict[str, Any]:
        """删除指定的配置文件

        注意：不能删除默认配置或当前激活的配置。

        Args:
            filename: 要删除的配置文件名

        Returns:
            包含删除结果的字典
        """
        # 禁止删除默认配置
        if filename == self.DEFAULT_CONFIG:
            return {
                "success": False,
                "error": "不能删除默认配置文件"
            }

        # 自动补全文件名
        if not filename.endswith('.yaml') and not filename.endswith('.yml'):
            filename = f"{filename}.yaml"

        config_path = self.configs_dir / filename

        if not config_path.exists():
            return {
                "success": False,
                "error": f"配置文件 {filename} 不存在"
            }

        # 检查是否是当前激活的配置
        if self.active_config.exists():
            try:
                active_content = self.active_config.read_text(encoding='utf-8')
                config_content = config_path.read_text(encoding='utf-8')
                if active_content.strip() == config_content.strip():
                    return {
                        "success": False,
                        "error": "不能删除当前激活的配置，请先切换到其他配置"
                    }
            except Exception:
                pass

        try:
            config_path.unlink()
            return {
                "success": True,
                "message": f"已删除配置文件: {filename}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_config_section(self, section: str) -> Optional[Dict[str, Any]]:
        """获取配置的特定节

        Args:
            section: 配置节名称（如 "server", "selected_module"）

        Returns:
            配置节字典，不存在则返回 None
        """
        config = self.get_merged_config()
        return config.get(section)

    def get_selected_module(self, module_type: str) -> Optional[str]:
        """获取选中的模块

        Args:
            module_type: 模块类型（如 "ASR", "TTS", "LLM", "VAD"）

        Returns:
            选中的模块名称
        """
        selected = self.get_config_section("selected_module")
        if selected:
            return selected.get(module_type)
        return None

    def update_active_config(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """更新激活配置的特定字段

        只更新指定的字段，保留其他字段不变。

        Args:
            updates: 要更新的配置字段

        Returns:
            包含更新结果的字典
        """
        try:
            # 读取当前激活配置
            current = {}
            if self.active_config.exists():
                with open(self.active_config, 'r', encoding='utf-8') as f:
                    current = yaml.safe_load(f) or {}

            # 深度合并更新
            def deep_merge(base: Dict, override: Dict) -> Dict:
                result = base.copy()
                for key, value in override.items():
                    if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                        result[key] = deep_merge(result[key], value)
                    else:
                        result[key] = value
                return result

            merged = deep_merge(current, updates)

            # 保存更新后的配置
            with open(self.active_config, 'w', encoding='utf-8') as f:
                yaml.dump(merged, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

            return {
                "success": True,
                "requires_restart": True,
                "message": "配置已更新，需要重启服务生效"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
