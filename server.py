"""
My Agent — 轻量 Web 服务
为 index.html 提供 API 接口
"""
import os
import sys
import json
import asyncio
import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='.', static_url_path='')

# ═══ 延迟初始化 Agent ═══
_agent_initialized = False
_registry = None
_skills = []

def init_agent():
    global _agent_initialized, _registry, _skills
    if _agent_initialized:
        return
    import config
    from tools.registry import registry
    import tools.builtin_compat
    from skills.loader import load_all_skills
    _registry = registry
    _skills = load_all_skills()
    _agent_initialized = True


# ═══ 页面路由 ═══

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


# ═══ API 路由 ═══

@app.route('/api/status')
def api_status():
    """获取 Agent 状态"""
    init_agent()
    from manage.tool_manager import ToolManager
    from manage.skill_manager import SkillManager
    from manage.memory_manager import MemoryManager

    tool_mgr = ToolManager(_registry)
    skill_mgr = SkillManager()
    mem_mgr = MemoryManager()

    tools_data = tool_mgr.list_by_category()
    skills_data = skill_mgr.list_skills()
    mem_stats = mem_mgr.get_stats()

    return jsonify({
        'status': 'ok',
        'tools': tools_data.get('categories', {}),
        'tool_stats': tool_mgr.get_stats(),
        'skills': skills_data.get('skills', []),
        'memory_stats': mem_stats,
    })


@app.route('/api/chat', methods=['POST'])
def api_chat():
    """对话接口"""
    init_agent()
    data = request.get_json(force=True)
    message = data.get('message', '').strip()
    session_id = data.get('session_id', 'web-default')

    if not message:
        return jsonify({'error': '消息不能为空'}), 400

    import config
    from core.conversation import Conversation

    try:
        conv = Conversation(session_id=session_id, restore=True)
        progress_log = []

        def on_progress(msg):
            progress_log.append(msg)

        def on_confirm(cmd):
            # Web 模式下默认拒绝高风险操作
            return False

        result = asyncio.run(conv.send(
            message,
            on_confirm=on_confirm,
            on_progress=on_progress,
        ))

        response = result.get('response', '(无回复)')
        tool_calls = result.get('tool_calls', [])
        stats = result.get('stats', {})

        # 附加进度日志
        result_data = {
            'response': response,
            'tool_calls': tool_calls,
            'stats': stats,
            '_progress': progress_log,
        }

        asyncio.run(conv.cleanup())
        return jsonify(result_data)

    except Exception as e:
        return jsonify({
            'response': f'❌ Agent 执行出错: {str(e)}',
            'tool_calls': [],
            'stats': {},
            '_progress': [],
        }), 500


@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'time': datetime.datetime.now().isoformat()})


# ═══════════════════════════════════════════════════
# 工具管理 API
# ═══════════════════════════════════════════════════

@app.route('/api/tools')
def api_tools_list():
    """列出所有工具（按分类分组）"""
    init_agent()
    from manage.tool_manager import ToolManager
    mgr = ToolManager(_registry)
    return jsonify(mgr.list_by_category())


@app.route('/api/tools/search')
def api_tools_search():
    """搜索工具"""
    keyword = request.args.get('q', '')
    init_agent()
    from manage.tool_manager import ToolManager
    mgr = ToolManager(_registry)
    return jsonify(mgr.search(keyword))


@app.route('/api/tools/<name>/toggle', methods=['POST'])
def api_tools_toggle(name):
    """启用/禁用工具"""
    init_agent()
    data = request.get_json(force=True)
    enabled = data.get('enabled', True)
    from manage.tool_manager import ToolManager
    mgr = ToolManager(_registry)
    return jsonify(mgr.toggle(name, enabled))


@app.route('/api/tools/auto-configure', methods=['POST'])
def api_tools_auto():
    """一键自动配置"""
    init_agent()
    from manage.tool_manager import ToolManager
    mgr = ToolManager(_registry)
    return jsonify(mgr.auto_configure())


# ═══════════════════════════════════════════════════
# 技能管理 API
# ═══════════════════════════════════════════════════

@app.route('/api/skills')
def api_skills_list():
    """列出所有技能"""
    from manage.skill_manager import SkillManager
    mgr = SkillManager()
    return jsonify(mgr.list_skills())


@app.route('/api/skills/<name>')
def api_skills_read(name):
    """读取技能内容"""
    from manage.skill_manager import SkillManager
    mgr = SkillManager()
    return jsonify(mgr.read_skill(name))


@app.route('/api/skills', methods=['POST'])
def api_skills_create():
    """创建新技能"""
    data = request.get_json(force=True)
    from manage.skill_manager import SkillManager
    mgr = SkillManager()
    return jsonify(mgr.create_skill(data.get('name', ''), data.get('description', '')))


@app.route('/api/skills/<name>', methods=['DELETE'])
def api_skills_delete(name):
    """删除技能"""
    from manage.skill_manager import SkillManager
    mgr = SkillManager()
    return jsonify(mgr.delete_skill(name, confirm=True))


# ═══════════════════════════════════════════════════
# 记忆管理 API
# ═══════════════════════════════════════════════════

@app.route('/api/memory')
def api_memory_list():
    """列出所有记忆"""
    from manage.memory_manager import MemoryManager
    mgr = MemoryManager()
    return jsonify(mgr.list_daily_memories())


@app.route('/api/memory/search')
def api_memory_search():
    """搜索记忆"""
    keyword = request.args.get('q', '')
    from manage.memory_manager import MemoryManager
    mgr = MemoryManager()
    return jsonify(mgr.search_memories(keyword))


@app.route('/api/memory/stats')
def api_memory_stats():
    """记忆统计"""
    from manage.memory_manager import MemoryManager
    mgr = MemoryManager()
    return jsonify(mgr.get_stats())


@app.route('/api/memory/<filename>')
def api_memory_read(filename):
    """读取记忆内容"""
    from manage.memory_manager import MemoryManager
    mgr = MemoryManager()
    return jsonify(mgr.read_memory(filename))


@app.route('/api/memory/<filename>', methods=['DELETE'])
def api_memory_delete(filename):
    """删除记忆"""
    from manage.memory_manager import MemoryManager
    mgr = MemoryManager()
    return jsonify(mgr.delete_memory(filename, confirm=True))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8080)
    parser.add_argument('--host', default='0.0.0.0')
    args = parser.parse_args()

    print(f'\n🤖 My Agent v1.3.1 Web 服务启动')
    print(f'   地址: http://localhost:{args.port}')
    print(f'   API:  http://localhost:{args.port}/api/chat')
    print(f'   健康: http://localhost:{args.port}/api/health')
    print()

    app.run(host=args.host, port=args.port, debug=False)
