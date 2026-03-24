import os
from enum import Enum
from pathlib import Path
from qfluentwidgets import (
    QConfig,
    ConfigItem,
    RangeConfigItem,
    OptionsConfigItem,
    BoolValidator,
    RangeValidator,
    OptionsValidator,
    ConfigSerializer,
)


class ThemeMode(str,Enum):
    LIGHT = "Light"
    DARK = "Dark"
    AUTO = "Auto"


class AppConfig(QConfig):
    """B.1 配置服务"""

    # --- 1.1 基础配置 ---
    isFullUpdated = ConfigItem("Basic", "IsFullUpdated", False, BoolValidator())
    logDir = ConfigItem("Basic", "LogDir", "logs")
    isDownloadDebug = ConfigItem("Basic", "IsDownloadDebug", True, BoolValidator())
    # 允许配置日志等级: DEBUG, INFO, WARNING, ERROR
    logLevel = OptionsConfigItem(
        "Basic",
        "LogLevel",
        "INFO",
        OptionsValidator(["DEBUG", "INFO", "WARNING", "ERROR"]),
    )
    dataDir = ConfigItem("Basic", "DataDir", "data")
    concurrentTasks = RangeConfigItem(
        "Basic", "ConcurrentTasks", 4, RangeValidator(1, 16)
    )
    retryCount = RangeConfigItem("Basic", "RetryCount", 3, RangeValidator(0, 10))

    # --- 1.2 主题配置 (独立项) ---
    themeMode = OptionsConfigItem(
        "Appearance",
        "ThemeMode",
        ThemeMode.AUTO,
        OptionsValidator(ThemeMode),
        ConfigSerializer(),
    )
    themeColor = ConfigItem("Appearance", "ThemeColor", "#0078d4")  # 主题色独立配置

    # --- 1.3 阅读配置 ---
    imageZoom = RangeConfigItem("Reading", "ImageZoom", 100, RangeValidator(10, 500))
    imageRotation = OptionsConfigItem(
        "Reading", "ImageRotation", 0, OptionsValidator([0, 90, 180, 270])
    )
    scrollSpeed = RangeConfigItem("Reading", "ScrollSpeed", 5, RangeValidator(1, 20))


# 单例模式
cfg = AppConfig()


def init_config():
    """初始化并加载配置"""
    cfg.load("config.json")
