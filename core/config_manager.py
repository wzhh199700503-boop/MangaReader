import json
import os
import threading

class ConfigManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ConfigManager, cls).__new__(cls)
            return cls._instance

    def __init__(self, config_path="config.json"):
        if hasattr(self, '_initialized'): return
        self.config_path = config_path
        self._config = {}
        self._load_defaults()
        self.load()
        self._initialized = True

    def _load_defaults(self):
        """默认配置"""
        self._config = {
            "is_full_synced": False,
            "debug_mode": True,
            "last_sync_date": ""
        }

    def load(self):
        with self._lock:
            if os.path.exists(self.config_path):
                try:
                    with open(self.config_path, "r", encoding="utf-8") as f:
                        self._config.update(json.load(f))
                except Exception as e:
                    print(f"读取配置失败: {e}")

    def save(self):
        with self._lock:
            try:
                os.makedirs(os.path.dirname(os.path.abspath(self.config_path)), exist_ok=True)
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump(self._config, f, indent=4, ensure_ascii=False)
            except Exception as e:
                print(f"保存配置失败: {e}")

    def get(self, key, default=None):
        with self._lock:
            return self._config.get(key, default)

    def set(self, key, value):
        with self._lock:
            self._config[key] = value
            # 每次设置后自动保存，确保数据安全
            self.save()