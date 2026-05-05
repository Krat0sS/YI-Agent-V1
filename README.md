# ☯️ 易Agent v1.4

**个人元操作系统智能体** — 以大衍筮法为决策底座、以 skill.md 为核心进化心脏的"活系统"

> "易有太极，是生两仪，两仪生四象，四象生八卦，八卦定吉凶，吉凶生大业。"

## 快速开始

### 1. 环境要求
- Python 3.10+
- Windows 10/11（推荐）

### 2. 安装

```powershell
# 双击 setup.bat，或手动执行：
setup.bat
```

自动完成：创建虚拟环境 → 安装依赖（使用国内镜像加速）→ 生成 .env 配置文件

### 3. 配置 API

编辑 `.env` 文件，填入你的 API Key：

```env
LLM_API_KEY=your-api-key-here
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

### 4. 启动

```powershell
# 双击 启动MyAgent.bat，或手动执行：
启动MyAgent.bat
```

浏览器会自动打开 Streamlit 可视化界面。

## 项目结构

```
YI-Agent-V1/
├── main.py                 # CLI 入口（交互式/Web/单次查询）
├── config.py               # 全局配置
├── app.py                  # Streamlit 可视化控制台
├── setup.bat               # 环境初始化脚本
├── 启动MyAgent.bat          # 一键启动脚本
├── requirements.txt        # 依赖列表
├── .env.example            # 环境变量模板
│
├── core/                   # 核心引擎
│   ├── conversation.py     # 对话管理器（五层易经流水线）
│   ├── dayan.py            # ☯️ 大衍筮法决策引擎（六爻十八变）
│   ├── intent_router.py    # 🧠 意图路由（BM25粗筛 + LLM精排）
│   ├── orchestrator.py     # 🔄 五行编排器（相生加权排序）
│   ├── wanwu.py            # 🌱 万物生成器（两两相错组合）
│   ├── temporal.py         # 🕐 时辰感知（十二时辰精力注入）
│   ├── change_engine.py    # ⚡ 变爻恢复引擎（失败自动重试/回滚）
│   ├── sub_agent.py        # 🤖 子Agent框架（上下文隔离+工具权限最小化）
│   ├── bm25.py             # BM25 文本匹配
│   └── llm.py              # LLM 客户端
│
├── tools/
│   ├── registry.py         # ToolRegistry 工具注册中心（49个工具）
│   ├── builtin.py          # 工具定义
│   └── builtin_compat.py   # 旧工具桥接
│
├── skills/                 # 技能系统（skill.md 驱动）
│   ├── loader.py           # 技能加载器（扫描+解析 SKILL.md）
│   ├── executor.py         # 技能执行器
│   ├── desktop-organize/   # 种子技能：桌面整理
│   ├── file-search/        # 种子技能：文件搜索
│   └── web-research/       # 种子技能：网络研究
│
├── memory/
│   └── memory_system.py    # 记忆系统
│
├── data/
│   └── execution_log.py    # 执行日志 SQLite（路由进化燃料）
│
├── security/
│   └── context_sanitizer.py # 安全模块（[EXTERNAL] 标签防护）
│
└── channels/
    └── webchat.py          # Flask Web 界面
```

## 核心架构：五层易经流水线

```
用户输入
    ↓
[1] ☯️ 大衍筮法（六爻十八变 → 完整卦象 → 行动建议）
    ↓ 分二→挂一→揲四→归奇，四营而成易，十有八变而成卦
[2] 🕐 时辰感知（十二时辰 → 精力水平注入）
    ↓
[3] 🌱 万物生成器（无技能匹配时，两两相错生成临时组合）
    ↓
[4] 🔄 五行编排器（相生加权排序 + 通关化解）
    ↓
[5] ⚡ 变爻恢复（工具失败后 → 老阳/老阴变爻 → 自动重试/回滚）
```

### 大衍筮法决策引擎

基于《周易·系辞上》的大衍筮法，映射到 Agent 决策：

| 大衍步骤 | Agent 决策 | 说明 |
|---------|-----------|------|
| 分而为二 | 工具按相关性分组 | 语义映射 + n-gram 双重匹配 |
| 挂一以象三 | 选出主工具 | 匹配度最高的工具 |
| 揲之以四 | 四维评估 | 能力/成本/风险/历史 |
| 归奇于扐 | 余数 → 爻性判定 | 老阳/少阳/少阴/老阴 |
| 四营而成易 | 一爻判定 | 四步完成一个决策维度 |
| 十有八变而成卦 | 完整卦象 | 6爻×3变=18变，六十四卦全覆盖 |

六爻对应决策链的六个维度：
- **初爻（反馈层）**：执行结果是否满足预期
- **二爻（执行层）**：执行过程中是否需要干预
- **三爻（参数层）**：工具的参数怎么调
- **四爻（选择层）**：具体用哪个工具
- **五爻（编排层）**：多个工具的执行顺序
- **上爻（战略层）**：这个任务值不值得做

### 路由进化闭环

```
用户说一句话
    ↓
意图分类器（simple / medium / complex）
    ↓
┌── simple → 直接调工具
├── medium → BM25粗筛 → LLM精排 → 命中技能？→ 是：极速执行
│                                → 否：分解任务
└── complex → 分解任务 → 子Agent编排（步骤>=3且有依赖）
                ↓
         执行完成
                ↓
    ┌── 成功且步骤>=2 → 自动沉淀为 skill.md（下次直接命中）
    └── 写入 execution_log.db（路由进化燃料）
```

**越用越强**：第一次遇到"整理桌面"→ 走完整分解流程 → 自动生成 skill.md → 第二次再说类似指令 → 直接命中技能 → 跳过推理，省 90% token。

### 子Agent框架

复杂任务自动拆分为多个子Agent并行/串行执行：

- **上下文隔离**：每个子Agent拥有全新的对话历史，不污染主Agent
- **工具权限最小化**：只暴露任务所需的工具，不是全部49个
- **输出净化**：子Agent返回结果用 `[EXTERNAL]` 标签包裹，防止 Prompt Injection
- **自动沉淀**：编排成功后，自动提炼为可复用的 skill.md

## 使用方式

### CLI 模式
```powershell
python main.py                    # 交互式对话
python main.py "帮我整理桌面"      # 单次查询
python main.py --skills           # 查看已加载技能
python main.py --stats            # 查看执行统计
```

### Web 模式
```powershell
python main.py --web              # Flask Web 界面（端口 8080）
```

### Streamlit 模式（推荐）
```powershell
启动MyAgent.bat                   # 双击启动
# 或手动：streamlit run app.py
```

## 核心特性

- **☯️ 大衍筮法** — 六爻十八变，六十四卦全覆盖，替代传统静态路由
- **🎯 技能系统** — skill.md 驱动，第一次慢、第二次快，越用越强
- **🤖 子Agent编排** — 复杂任务自动拆分，并行执行，结果汇总
- **🔄 五行编排** — 相生加权排序，自动优化工具执行顺序
- **🌱 万物生成** — 无技能匹配时，两两相错生成临时组合
- **🕐 时辰感知** — 十二时辰精力模型，智能调整任务策略
- **⚡ 变爻恢复** — 工具失败后自动重试/回滚，老阳变阴、老阴变阳
- **📊 路由进化** — execution_log.db 记录一切，自动分析误路由和新技能候选
- **🔒 安全模块** — [EXTERNAL] 标签隔离外部内容，Prompt Injection 防护
- **🔧 ToolRegistry** — 49 个工具自动注册，动态 Schema，优雅降级

## 路线图

- [x] Phase 0：大衍筮法引擎 + 五层易经流水线
- [x] Phase 1：ToolRegistry + skill.md 骨架 + execution_log.db
- [x] Phase 2：子Agent框架 + skill.md 自动沉淀 + 路由进化引擎
- [ ] Phase 3：跨设备适配器框架（手机端 Platform）
- [ ] Phase 4：记忆分层架构（SQLite FTS5 + LRU 热缓存）
- [ ] Phase 5：人格连续性 + 安全审计 + 信任模型

## 许可证

MIT License
