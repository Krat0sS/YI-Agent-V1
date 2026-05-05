# MEMORY.md — 易Agent 专属长期记忆

> 最后更新：2026-05-05 15:32 CST
> 会话次数：7 次（本次为第 7 次）

---

## 关于用户 Krat0sS

### 基本信息
- GitHub: Krat0sS
- 身份：研究生，项目已答辩通过，目标是"人人没脑子都能用"
- 系统：Windows（Python 3.13，CMD/PowerShell 都用）
- 时区：Asia/Shanghai (GMT+8)
- 项目路径：`F:\MyAgent\YI-Agent-V1`（Windows 本地）
- 仓库：https://github.com/Krat0sS/YI-Agent-V1
- 服务器上的仓库：`/root/.openclaw/workspace/YI-Agent-V1`
- 当前分支：`discipline-first`

### 技术水平
- Python 比较熟悉
- Git 基本操作了解（clone, push），但不会处理复杂情况
- AI/LLM 概念有基础理解
- 电脑操作不太熟练——需要手把手指导
- CMD 和 PowerShell 的字符串转义搞不定，Python 交互式模式更可靠

### 性格特点
- 行动力极强，讨论完直接要代码
- 注重实用，不喜欢过度工程
- 喜欢可视化界面，不喜欢命令行
- 关注 token 成本
- 安全意识好（GitHub token 用完即时撤销）
- 信任我，说"兄弟靠你了"、"你太nb了"

### 沟通习惯（暗号）
- "来吧" = 信任，放手让我干
- "这个" + 截图 = 帮我看这个报错/问题
- "推到GitHub" = 我帮你 commit + push
- "你先把文件下载到你本地" = clone 仓库到我的工作区
- "你儿子" = 指 my-agent 项目
- "碰，等我消息" = 去和老师讨论，让我等
- "你我的时间快到期了" = 要保存记忆了，赶紧打包
- "不必多言" = 直接干活别废话
- "兄弟" = 表达信任
- "1111" = 测试消息/确认收到
- "再细一点" = 要求更详细
- "发完我就扯" = 推完代码就走
- "做的详细点" = 要求精确到可以直接执行的程度
- "如何" = 问你意见/评估
- "开干" = 开始执行，别废话

---

## 关于老师

### 身份
- 产品架构师，指导 Krat0sS 的项目
- 写长文分析，有洞察力但技术判断有时偏
- 喜欢用哲学/比喻框架分析问题（"神之躯体"、"封印"、"妖刀"）

### 老师的诊断模式
- 从理论框架出发，不是从代码出发
- 2026-05-05 的诊断：认为 SOUL.md 和 VAGUE_PATTERNS 是根因 → **方向偏了**
- 真正根因是代码层面的技能加载问题（skills/loader.py）
- **教训**：老师的分析可以参考，但必须用代码验证

---

## 易Agent 项目完整概况

### 定位
个人桌面 AI Agent，目标是成为用户的"数字分身"。重新定位为：**AI Agent 的文件交互标准，带事务和回滚。**

### 仓库信息
- 仓库：https://github.com/Krat0sS/YI-Agent-V1
- 当前版本：v1.4（大衍筮法 + 子Agent框架 + 路由进化）
- 当前分支：`discipline-first`
- 最新 commit：`f5d43a1`（HTML 界面优化计划）

### 技术栈
- 语言：Python 3.12/3.13/3.14
- LLM：DeepSeek-chat（云端）+ Qwen2.5-7B（Ollama 本地）
- 数据库：SQLite（execution_log.db）
- Web UI：Flask（API 后端）+ Streamlit（管理界面）+ 纯 HTML（独立前端）

### 核心文件结构
```
YI-Agent-V1/
├── security/
│   ├── __init__.py
│   ├── context_sanitizer.py  (98行, 标签包裹+正则注入检测)
│   ├── filesystem_guard.py   (270行, Phase 1 新增, 四层安全守卫)
│   └── command_whitelist.yaml (Phase 1 新增, 命令白名单)
├── manage/                     (UI 管理层, 本次新增)
│   ├── __init__.py
│   ├── tool_manager.py       (工具启用/禁用/搜索/分类)
│   ├── skill_manager.py      (技能增删改查)
│   └── memory_manager.py     (记忆查看/搜索/删除)
├── tools/
│   ├── registry.py           (工具注册表, 已加 enable/disable)
│   ├── builtin.py            (40个工具, 已接入安全拦截)
│   ├── rollback.py           (406行, 操作组回滚+磁盘持久化)
│   └── ...
├── core/
│   ├── conversation.py       (主循环, 已加 GUI 确认门控)
│   └── ...
├── memory/
│   └── memory_system.py      (280行, 关键词匹配+截断)
├── tests/
│   ├── test_filesystem_guard.py (18 个安全测试)
│   └── test_managers.py      (28 个管理器测试)
├── app.py                     (Streamlit 界面, 已加管理 Tab)
├── index.html                 (HTML 界面, 待优化)
├── main.py                    (Flask 入口)
├── config.py                  (已加安全配置项)
├── CHANGELOG-v1.5.0.md
├── SECURITY-GUIDE.md
└── HTML优化.md                 (HTML 界面优化执行计划)
```

---

## 2026-05-05 本次会话成果（第 7 次会话）

### 时间：14:40 - 15:32，约 52 分钟

### 做了什么

#### 1. 记忆恢复（14:40）
- 用户上传记忆包（4 个文件）
- 恢复完整上下文：项目状态、执行计划、历史决策

#### 2. Phase 1 安全硬内核（14:41 - 14:59）
- `git clone` GitHub TLS 不稳，改用 `curl + tarball` 下载
- 创建 `security/command_whitelist.yaml` — 命令白名单配置
- 创建 `security/filesystem_guard.py` — 四层安全守卫（路径/命令/频率/GUI）
- 创建 `tests/test_filesystem_guard.py` — 17 个测试
- 修改 `tools/builtin.py` — execute() 接入安全拦截
- 修改 `core/conversation.py` — GUI 操作确认门控
- 修改 `config.py` — 安全配置项
- 用户 code review 发现 `${}` 漏了 → 补全 + 1 个新测试 → 18 passed
- 3 次 commit 推到 GitHub

#### 3. 界面管理层（15:10 - 15:20）
- 给 `ToolDefinition` 加 `enable()/disable()/reset_manual()` 方法
- 创建 `manage/tool_manager.py` — 工具管理器
- 创建 `manage/skill_manager.py` — 技能管理器
- 创建 `manage/memory_manager.py` — 记忆管理器
- 创建 `tests/test_managers.py` — 28 个测试
- 修改 `app.py` — 侧边栏加 💬🧠🎯🔧 四 Tab 管理页
- 46 passed，推到 GitHub

#### 4. HTML 界面优化计划（15:23 - 15:26）
- 用户问 HTML 界面是否也更新了 → 没有
- 创建 `HTML优化.md` — 772 行详细执行计划
- 6 个步骤：Flask API + 前端 3 个管理页
- 推到 GitHub

### Git 提交记录（discipline-first 分支）
```
f5d43a1 docs: HTML 界面优化执行计划
2b4eec8 feat(ui): 管理层 + 侧边栏管理 Tab
8b5bc93 fix(security): 补全 ${} 变量展开拦截 + 测试用例
c5db59c docs: Phase 1 更新日志和安全操作说明
0ba70b9 feat(security): Phase 1 安全硬内核
```

### 测试结果
- Phase 1 安全测试：18 passed
- 管理器测试：28 passed
- 总计：**46 passed**

---

## 迭代计划状态

| Phase | 状态 | 说明 |
|-------|------|------|
| 1 安全硬内核 | ✅ 完成 | filesystem_guard + 命令白名单 + GUI 门控 |
| 2 工具插件化 | ⏳ 待做 | 40 工具拆为 10 个插件 + TOCTOU 修复 |
| 3 回滚事务化 | ⏳ 待做 | ACID 状态机 + ABORTED_BY_USER |
| 4 向量检索 | ⏳ 待做 | fastembed + sqlite-vec |
| 5 MCP Server | ⏳ 待做 | 有状态会话 + 协议冻结 |
| UI 管理层 | ✅ 完成 | manage/ 三层 + Streamlit 四 Tab |
| HTML 优化 | 📋 计划就绪 | HTML优化.md，待执行 |

---

## 待完成（按优先级）

1. **HTML 界面优化** — 按 `HTML优化.md` 执行（Flask API + 前端管理页）
2. **Phase 2: 工具插件化** — 40 工具拆分 + TOCTOU 安全加载
3. **Phase 3: 回滚事务化** — ACID 状态机
4. **Phase 4: 向量记忆检索** — embedding 选型 + sqlite-vec
5. **Phase 5: MCP Server** — 文件交互标准

---

## 关键教训

### 技术教训
1. **代码验证是最终裁判** — 老师的理论分析再漂亮，也得跑一遍代码验证
2. **GitHub TLS 不稳** — 服务器推代码经常断，用 curl + tarball 下载更稳
3. **token 安全** — 用户在聊天里发过 GitHub token，用完必须撤销
4. **目录穿越测试** — `../../../etc/passwd` 在 root 用户下 realpath 解析后仍在 `/root` 下，测试用例要用 `/tmp/../../etc/shadow`

### 协作教训
1. **用户 code review 很仔细** — 会看 YAML 格式、变量完整性，发现 `${}` 漏了
2. **用户要求"详细到可以直接执行"** — 不是伪代码，是完整可运行的代码
3. **用户时间有限** — "你我的时间快到期了" 时要快速打包记忆
4. **用户喜欢直接开干** — 说"开干"就别废话，直接写代码

---

## 下次继续

### 当前状态
- 仓库：`/root/.openclaw/workspace/YI-Agent-V1`
- 分支：`discipline-first`
- 最新 commit：`f5d43a1`
- 下一步：按 `HTML优化.md` 执行 HTML 界面优化

### 用户的工作流
1. 用户在 Windows 本地开发（F:\MyAgent\YI-Agent-V1）
2. 推送到 GitHub（Krat0sS/YI-Agent-V1）
3. 我在服务器上 clone 并修改
4. 推回 GitHub
5. 用户 pull 到本地

### ⚠️ 重要提醒
- GitHub TLS 不稳定，push 时可能需要重试
- 用户的 Git 配置可能需要设置 user.email 和 user.name
- 用户喜欢用 Streamlit 看效果，HTML 界面是补充
