# v1.5.0 — Phase 1: 安全硬内核

> 日期：2026-05-05
> 分支：`discipline-first`
> 原则：默认拒绝，显式允许。安全拦截在代码层，零依赖 LLM。

---

## 新增文件

### `security/command_whitelist.yaml`
命令白名单配置。定义三级命令权限：
- `read_only` — 只读命令，直接放行（ls, cat, find, stat...）
- `write` — 写命令，放行但记录（mv, cp, mkdir...）
- `write_requires_confirm` — 高危命令，需用户二次确认（rm, chmod, chown...）
- `blocked_chars` — 危险字符，命令中不允许出现（; | & ` $() 等）
- `allowed_path_prefixes` — 文件操作允许的路径前缀

### `security/filesystem_guard.py`
文件系统安全守卫（270 行），四层安全检查：

| 层 | 功能 | 说明 |
|----|------|------|
| 1 | `check_path()` | 路径安全 — realpath 解析符号链接 + 白名单前缀校验 |
| 2 | `check_command()` | 命令安全 — 危险字符检测 + 白名单匹配 |
| 3 | `check_rate()` | 频率熔断 — 30秒内超过20次操作自动冻结 |
| 4 | `check_gui_operation()` | GUI 门控 — 高风险桌面/浏览器操作需确认 |

统一入口：`check_tool_call(tool_name, arguments, session_id)` — 在工具执行前调用。

### `tests/test_filesystem_guard.py`
17 个测试用例，覆盖：
- 路径安全（正常路径、白名单外、符号链接攻击、目录穿越、空路径）
- 命令安全（只读、写确认、分号注入、管道注入、反引号注入、$()注入、未知命令、空命令）
- 频率熔断（正常频率、突发高频）
- 统一入口（安全工具、危险命令）

---

## 修改文件

### `tools/builtin.py`
`execute()` 函数新增安全拦截逻辑：
```
工具调用 → 安全拦截器检查 → 通过则执行，不通过则返回 blocked
```

### `core/conversation.py`
`_execute_tool()` 方法新增 GUI 确认门控：
```
浏览器/桌面操作 → check_gui_operation() → 需确认则弹窗 → 用户拒绝则取消
```

### `config.py`
新增配置项：
```python
SECURITY_ENABLED = true          # 总开关
SECURITY_RATE_WINDOW = 30        # 频率窗口（秒）
SECURITY_RATE_MAX_OPS = 20       # 窗口内最大操作数
```

---

## 测试结果

```
17 passed in 0.06s

tests/test_filesystem_guard.py::TestPathSafety::test_normal_path_allowed PASSED
tests/test_filesystem_guard.py::TestPathSafety::test_path_outside_whitelist_blocked PASSED
tests/test_filesystem_guard.py::TestPathSafety::test_symlink_attack_blocked PASSED
tests/test_filesystem_guard.py::TestPathSafety::test_directory_traversal_blocked PASSED
tests/test_filesystem_guard.py::TestPathSafety::test_empty_path_blocked PASSED
tests/test_filesystem_guard.py::TestCommandSafety::test_read_command_allowed PASSED
tests/test_filesystem_guard.py::TestCommandSafety::test_write_command_confirm PASSED
tests/test_filesystem_guard.py::TestCommandSafety::test_command_injection_semicolon_blocked PASSED
tests/test_filesystem_guard.py::TestCommandSafety::test_command_injection_pipe_blocked PASSED
tests/test_filesystem_guard.py::TestCommandSafety::test_command_injection_backtick_blocked PASSED
tests/test_filesystem_guard.py::TestCommandSafety::test_command_injection_dollar_paren_blocked PASSED
tests/test_filesystem_guard.py::TestCommandSafety::test_unknown_command_blocked PASSED
tests/test_filesystem_guard.py::TestCommandSafety::test_empty_command_blocked PASSED
tests/test_filesystem_guard.py::TestRateLimit::test_normal_rate_allowed PASSED
tests/test_filesystem_guard.py::TestRateLimit::test_burst_rate_blocked PASSED
tests/test_filesystem_guard.py::TestToolCall::test_safe_tool_passes PASSED
tests/test_filesystem_guard.py::TestToolCall::test_dangerous_command_blocked PASSED
```

---

## 验证命令

```bash
# 1. 路径攻击拦截
python -c "from security.filesystem_guard import guard; print(guard.check_path('/etc/passwd'))"
# → safe=False

# 2. 命令注入拦截
python -c "from security.filesystem_guard import guard; print(guard.check_command('cat file; rm -rf /'))"
# → safe=False, reason=危险字符

# 3. 正常命令放行
python -c "from security.filesystem_guard import guard; print(guard.check_command('ls -la'))"
# → safe=True

# 4. 运行全部测试
python -m pytest tests/test_filesystem_guard.py -v
```
