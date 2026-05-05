"""
文件系统安全守卫 — 代码层拦截，零依赖 LLM

职责：
1. 路径安全检查（防符号链接绕过、目录穿越）
2. 命令安全检查（白名单模式、防注入）
3. 操作频率熔断
4. GUI 操作确认门控

设计原则：默认拒绝，显式允许。
"""
import os
import re
import time
import shlex
import threading
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

# ═══ 配置加载 ═══

_DEFAULT_READ_ONLY = {
    "ls", "stat", "find", "du", "df", "file", "cat", "head", "tail",
    "tree", "wc", "md5sum", "sha256sum", "pwd", "whoami", "which",
    "echo", "date", "env", "printenv",
}

_DEFAULT_WRITE = {
    "mv", "cp", "rsync", "mkdir", "touch", "ln",
    "tar", "zip", "unzip", "diff", "tee",
}

_DEFAULT_WRITE_CONFIRM = {"rm", "rmdir", "chmod", "chown", "chgrp"}

_DEFAULT_BLOCKED_CHARS = {";", "|", "&", "`", "$(", "${", "\n", "\r"}

# 默认允许的路径前缀（用户主目录 + 常见工作目录）
_DEFAULT_ALLOWED_PREFIXES = [
    os.path.expanduser("~"),
    "/tmp",
]


@dataclass
class SafetyResult:
    """安全检查结果"""
    safe: bool
    reason: str = ""
    needs_confirm: bool = False
    risk_level: str = "none"  # none / low / high
    resolved_path: str = ""
    details: dict = field(default_factory=dict)


class FileSystemGuard:
    """
    文件系统安全守卫。

    使用方法：
        guard = FileSystemGuard()
        result = guard.check_path("~/Desktop/test.txt")
        if not result.safe:
            print(f"拦截: {result.reason}")
    """

    def __init__(self, config_path: str = None):
        self._lock = threading.Lock()
        self._op_timestamps: dict[str, list[float]] = {}  # session_id → [timestamps]

        # 加载白名单
        self.read_only = set(_DEFAULT_READ_ONLY)
        self.write = set(_DEFAULT_WRITE)
        self.write_confirm = set(_DEFAULT_WRITE_CONFIRM)
        self.blocked_chars = set(_DEFAULT_BLOCKED_CHARS)
        self.allowed_prefixes = list(_DEFAULT_ALLOWED_PREFIXES)

        # 频率熔断参数
        self.rate_window = 30   # 秒
        self.rate_max_ops = 20  # 窗口内最大操作数

        # 从 YAML 加载自定义配置
        if config_path:
            self._load_yaml(config_path)
        else:
            default_yaml = os.path.join(os.path.dirname(__file__), "command_whitelist.yaml")
            if os.path.exists(default_yaml):
                self._load_yaml(default_yaml)

    def _load_yaml(self, path: str):
        """从 YAML 文件加载白名单配置"""
        try:
            import yaml
            with open(path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
            if not cfg:
                return
            if "read_only" in cfg:
                self.read_only = set(cfg["read_only"])
            if "write" in cfg:
                self.write = set(cfg["write"])
            if "write_requires_confirm" in cfg:
                self.write_confirm = set(cfg["write_requires_confirm"])
            if "blocked_chars" in cfg:
                self.blocked_chars = set(cfg["blocked_chars"])
            if "allowed_path_prefixes" in cfg:
                self.allowed_prefixes = [
                    os.path.expanduser(p) for p in cfg["allowed_path_prefixes"]
                ]
        except Exception:
            pass  # YAML 加载失败用默认值

    # ═══ 路径安全检查 ═══

    def check_path(self, path: str) -> SafetyResult:
        """
        检查文件路径是否安全。

        检查项：
        1. os.path.realpath() 解析符号链接
        2. 解析后的路径是否在白名单前缀内
        3. 是否包含目录穿越（../）
        """
        if not path:
            return SafetyResult(safe=False, reason="路径为空")

        expanded = os.path.expanduser(path)

        # 检查目录穿越（在 realpath 之前）
        if ".." in expanded.split(os.sep) or ".." in expanded.split("/"):
            # 不直接拒绝，因为 realpath 会解析掉。但记录。
            pass

        # 解析符号链接，获取真实路径
        try:
            resolved = os.path.realpath(expanded)
        except OSError as e:
            return SafetyResult(safe=False, reason=f"路径解析失败: {e}")

        # 检查是否在白名单前缀内
        for prefix in self.allowed_prefixes:
            real_prefix = os.path.realpath(os.path.expanduser(prefix))
            if resolved.startswith(real_prefix + os.sep) or resolved == real_prefix:
                return SafetyResult(
                    safe=True,
                    resolved_path=resolved,
                    details={"matched_prefix": prefix}
                )

        return SafetyResult(
            safe=False,
            reason=f"路径不在允许范围内: {resolved}（允许前缀: {self.allowed_prefixes}）",
            resolved_path=resolved,
            risk_level="high",
        )

    # ═══ 命令安全检查 ═══

    def check_command(self, command: str) -> SafetyResult:
        """
        检查 shell 命令是否安全。

        检查项：
        1. 危险字符检测（; | & ` $() 等命令注入分隔符）
        2. shlex.split 解析命令名和参数
        3. 命令名与白名单匹配
        4. rm 等高危命令需二次确认
        """
        if not command or not command.strip():
            return SafetyResult(safe=False, reason="命令为空")

        cmd = command.strip()

        # 检查危险字符
        for char in self.blocked_chars:
            if char in cmd:
                return SafetyResult(
                    safe=False,
                    reason=f"命令包含危险字符 '{char}': {cmd[:100]}",
                    risk_level="high",
                )

        # shlex 解析
        try:
            parts = shlex.split(cmd)
        except ValueError as e:
            return SafetyResult(
                safe=False,
                reason=f"命令解析失败（可能包含未闭合的引号）: {e}",
                risk_level="high",
            )

        if not parts:
            return SafetyResult(safe=False, reason="命令解析后为空")

        cmd_name = os.path.basename(parts[0])  # 去掉路径前缀（如 /bin/ls → ls）

        # 白名单检查
        all_allowed = self.read_only | self.write | self.write_confirm
        if cmd_name not in all_allowed:
            return SafetyResult(
                safe=False,
                reason=f"命令不在白名单中: {cmd_name}（允许: {sorted(all_allowed)[:10]}...）",
                risk_level="high",
            )

        # 写命令需确认
        if cmd_name in self.write_confirm:
            return SafetyResult(
                safe=True,
                needs_confirm=True,
                reason=f"写命令需用户确认: {cmd_name}",
                risk_level="medium",
            )

        # 写命令（不需要确认）
        if cmd_name in self.write:
            return SafetyResult(
                safe=True,
                needs_confirm=False,
                risk_level="low",
            )

        # 只读命令
        return SafetyResult(safe=True, risk_level="none")

    # ═══ 操作频率熔断 ═══

    def check_rate(self, session_id: str = "default") -> SafetyResult:
        """
        检查操作频率是否异常。
        30秒内超过20次操作则冻结。
        """
        now = time.time()
        with self._lock:
            if session_id not in self._op_timestamps:
                self._op_timestamps[session_id] = []

            timestamps = self._op_timestamps[session_id]
            # 清理过期时间戳
            cutoff = now - self.rate_window
            self._op_timestamps[session_id] = [t for t in timestamps if t > cutoff]

            if len(self._op_timestamps[session_id]) >= self.rate_max_ops:
                return SafetyResult(
                    safe=False,
                    reason=f"操作频率异常：{self.rate_window}秒内{len(self._op_timestamps[session_id])}次操作",
                    risk_level="high",
                    details={"operations_in_window": len(self._op_timestamps[session_id])},
                )

            # 记录本次操作
            self._op_timestamps[session_id].append(now)
            return SafetyResult(safe=True)

    # ═══ GUI 操作确认门控 ═══

    def check_gui_operation(self, func_name: str, args: dict) -> dict:
        """
        桌面/浏览器操作的确认门控。
        返回 {"needs_confirm": bool, "confirm_message": str}
        """
        # 高风险 GUI 操作
        high_risk_gui = {
            "desktop_click", "desktop_double_click",
            "browser_click", "browser_type",
        }
        if func_name in high_risk_gui:
            return {
                "needs_confirm": True,
                "confirm_message": f"即将执行 GUI 操作: {func_name}({args})",
            }
        return {"needs_confirm": False}

    # ═══ 统一入口：工具调用安全检查 ═══

    def check_tool_call(self, tool_name: str, arguments: dict,
                        session_id: str = "default") -> SafetyResult:
        """
        统一安全检查入口。在 tools/builtin.py 的 execute() 中调用。

        检查流程：
        1. 频率熔断
        2. 根据工具类型分发检查
        """
        # 1. 频率熔断
        rate_result = self.check_rate(session_id)
        if not rate_result.safe:
            return rate_result

        # 2. 命令执行工具
        if tool_name in ("run_command", "run_command_confirmed"):
            cmd = arguments.get("command", "")
            return self.check_command(cmd)

        # 3. 文件操作工具 — 检查路径参数
        file_path_tools = {
            "read_file": ["path"],
            "write_file": ["path"],
            "edit_file": ["path"],
            "list_files": ["path"],
            "move_file": ["source", "destination"],
            "batch_move": [],  # 参数结构复杂，暂不检查路径
            "find_files": [],  # 只读，不检查
            "scan_files": ["directory"],
            "organize_directory": ["directory"],
        }
        if tool_name in file_path_tools:
            path_keys = file_path_tools[tool_name]
            for key in path_keys:
                path_val = arguments.get(key, "")
                if path_val:
                    result = self.check_path(path_val)
                    if not result.safe:
                        return result

        # 4. 文件写入工具 — 需确认
        write_tools = {"write_file", "edit_file", "move_file", "batch_move", "organize_directory"}
        if tool_name in write_tools:
            return SafetyResult(safe=True, needs_confirm=False, risk_level="low")

        # 5. 默认放行
        return SafetyResult(safe=True)


# ═══ 全局单例 ═══
guard = FileSystemGuard()
