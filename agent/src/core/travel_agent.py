"""
ReAct 旅游助手 Agent
====================

基于 ReAct (Reasoning and Acting) 模式的旅游智能体实现。
"""

import json
import sys
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

# 添加父目录到路径以支持外部导入
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
AGENT_SRC_DIR = os.path.dirname(CURRENT_DIR)
if AGENT_SRC_DIR not in sys.path:
    sys.path.insert(0, AGENT_SRC_DIR)

# 使用绝对导入替代相对导入
from core.react_agent import ReActAgent, ToolInfo, Action, Thought, AgentState, ActionStatus
from config.config_manager import ConfigManager
from memory.manager import MemoryManager
from llm.client import LLMClient


def create_travel_tools(config_manager: ConfigManager) -> List[tuple]:
    """创建旅游助手工具列表"""
    from environment.travel_data import TravelData

    tools = []

    tools.append((
        ToolInfo(
            name="search_cities",
            description="根据用户兴趣、预算和季节偏好搜索匹配的城市",
            parameters={
                'type': 'object',
                'properties': {
                    'interests': {
                        'type': 'array',
                        'items': {'type': 'string'},
                        'description': '用户兴趣标签列表'
                    },
                    'budget_min': {'type': 'integer', 'description': '最低预算'},
                    'budget_max': {'type': 'integer', 'description': '最高预算'},
                    'season': {'type': 'string', 'description': '旅行季节'}
                }
            },
            required_params=[],
            category='travel',
            tags=['search', 'city', 'recommend']
        ),
        lambda interests=None, budget_min=None, budget_max=None, season=None:
            _search_cities(config_manager, interests, (budget_min, budget_max) if budget_min and budget_max else None, season)
    ))

    tools.append((
        ToolInfo(
            name="query_attractions",
            description="查询指定城市的景点信息",
            parameters={
                'type': 'object',
                'properties': {
                    'cities': {
                        'type': 'array',
                        'items': {'type': 'string'},
                        'description': '要查询的城市名称列表'
                    }
                },
                'required': ['cities']
            },
            required_params=['cities'],
            category='travel',
            tags=['query', 'attraction', 'scenic']
        ),
        lambda cities: _query_attractions(config_manager, cities)
    ))

    tools.append((
        ToolInfo(
            name="generate_route",
            description="为指定城市生成详细的旅游路线规划",
            parameters={
                'type': 'object',
                'properties': {
                    'city': {'type': 'string', 'description': '目标城市名称'},
                    'days': {'type': 'integer', 'description': '旅行天数，默认3天', 'default': 3}
                },
                'required': ['city']
            },
            required_params=['city'],
            category='travel',
            tags=['route', 'plan', 'schedule']
        ),
        lambda city, days=3: _generate_route(config_manager, city, days)
    ))

    tools.append((
        ToolInfo(
            name="calculate_budget",
            description="计算指定城市和天数的旅游预算",
            parameters={
                'type': 'object',
                'properties': {
                    'city': {'type': 'string', 'description': '目标城市'},
                    'days': {'type': 'integer', 'description': '旅行天数'}
                },
                'required': ['city', 'days']
            },
            required_params=['city', 'days'],
            category='travel',
            tags=['budget', 'cost', 'expense']
        ),
        lambda city, days: _calculate_budget(config_manager, city, days)
    ))

    tools.append((
        ToolInfo(
            name="get_city_info",
            description="获取指定城市的详细信息",
            parameters={
                'type': 'object',
                'properties': {
                    'city': {'type': 'string', 'description': '城市名称'}
                },
                'required': ['city']
            },
            required_params=['city'],
            category='travel',
            tags=['city', 'info', 'detail']
        ),
        lambda city: _get_city_info(config_manager, city)
    ))

    tools.append((
        ToolInfo(
            name="llm_chat",
            description="使用大语言模型进行对话回答",
            parameters={
                'type': 'object',
                'properties': {
                    'query': {'type': 'string', 'description': '用户问题'},
                    'context': {'type': 'string', 'description': '对话上下文'}
                },
                'required': ['query']
            },
            required_params=['query'],
            category='ai',
            tags=['chat', 'llm', 'ai']
        ),
        lambda query, context="": _llm_chat(config_manager, query, context)
    ))

    tools.append((
        ToolInfo(
            name="generate_city_recommendation",
            description="根据用户需求生成个性化城市推荐",
            parameters={
                'type': 'object',
                'properties': {
                    'user_query': {'type': 'string', 'description': '用户原始需求'},
                    'available_cities': {
                        'type': 'array',
                        'items': {'type': 'string'},
                        'description': '可选城市列表'
                    }
                },
                'required': ['user_query', 'available_cities']
            },
            required_params=['user_query', 'available_cities'],
            category='ai',
            tags=['recommend', 'city', 'llm']
        ),
        lambda user_query, available_cities: _generate_recommendation(config_manager, user_query, available_cities)
    ))

    tools.append((
        ToolInfo(
            name="generate_route_plan",
            description="根据城市景点信息生成详细路线规划",
            parameters={
                'type': 'object',
                'properties': {
                    'city': {'type': 'string', 'description': '目标城市'},
                    'days': {'type': 'integer', 'description': '旅行天数'},
                    'preferences': {'type': 'string', 'description': '用户偏好'}
                },
                'required': ['city', 'days']
            },
            required_params=['city', 'days'],
            category='ai',
            tags=['route', 'plan', 'llm']
        ),
        lambda city, days, preferences="": _generate_route_plan(config_manager, city, days, preferences)
    ))

    return tools


def _search_cities(config_manager, interests: List[str] = None,
                   budget: tuple = None, season: str = None) -> Dict[str, Any]:
    from environment.travel_data import TravelData
    env = TravelData(config_manager)
    return env.search_cities(interests, budget, season)


def _query_attractions(config_manager, cities: List[str]) -> Dict[str, Any]:
    from environment.travel_data import TravelData
    env = TravelData(config_manager)
    return env.query_attractions(cities)


def _generate_route(config_manager, city: str, days: int) -> Dict[str, Any]:
    from environment.travel_data import TravelData
    env = TravelData(config_manager)
    result = env.get_city_info(city)
    if not result.get('success'):
        return result

    city_info = result.get('info', {})
    attractions = city_info.get('attractions', [])

    route_plan = []
    for i in range(min(days, len(attractions))):
        attr = attractions[i] if i < len(attractions) else {'name': '自由活动'}
        route_plan.append({
            'day': i + 1,
            'attractions': [attr['name']] if isinstance(attr, dict) else [attr],
            'schedule': f'游览{attr.get("name", "自由活动")}'
        })

    return {
        'success': True,
        'city': city,
        'route_plan': route_plan,
        'total_cost_estimate': {
            'tickets': sum(a.get('ticket', 0) for a in attractions[:days]),
            'total': sum(a.get('ticket', 0) for a in attractions[:days]) + city_info.get('avg_budget_per_day', 400) * days
        }
    }


def _calculate_budget(config_manager, city: str, days: int) -> Dict[str, Any]:
    from environment.travel_data import TravelData
    env = TravelData(config_manager)
    return env.calculate_budget(city, days)


def _get_city_info(config_manager, city: str) -> Dict[str, Any]:
    from environment.travel_data import TravelData
    env = TravelData(config_manager)
    return env.get_city_info(city)


def _llm_chat(config_manager, query: str, context: str = "") -> Dict[str, Any]:
    llm_config = config_manager.get_default_model_config()
    llm_client = LLMClient(llm_config)

    messages = [{"role": "user", "content": query}]
    if context:
        messages.insert(0, {"role": "system", "content": context})

    result = llm_client.chat(messages)

    if isinstance(result, dict):
        if result.get('success') and 'content' in result:
            return {'success': True, 'response': result['content']}
        elif 'error' in result:
            return {'success': False, 'response': result['error']}
    return result


def _generate_recommendation(config_manager, user_query: str,
                             available_cities: List[str]) -> Dict[str, Any]:
    llm_config = config_manager.get_default_model_config()
    llm_client = LLMClient(llm_config)
    return llm_client.generate_travel_recommendation(user_query, "", available_cities)


def _generate_route_plan(config_manager, city: str, days: int,
                         preferences: str = "") -> Dict[str, Any]:
    city_info = config_manager.get_city_info(city)
    if not city_info:
        return {'success': False, 'error': f'未找到城市: {city}'}

    attractions = city_info.get('attractions', [])
    llm_config = config_manager.get_default_model_config()
    llm_client = LLMClient(llm_config)
    return llm_client.generate_route_plan(city, days, attractions, preferences)


class ReActTravelAgent:
    """ReAct 旅游助手 Agent"""

    def __init__(self, config_path: str = "config/llm_config.yaml",
                 model_id: Optional[str] = None,
                 max_steps: int = 10):
        self.config_manager = ConfigManager(config_path)

        memory_config = self.config_manager.agent_config.get('max_working_memory', 10)
        self.memory_manager = MemoryManager(
            max_working_memory=memory_config
        )

        # Get model config using the new method
        if model_id:
            llm_config = self.config_manager.get_model_config(model_id)
        else:
            llm_config = self.config_manager.get_default_model_config()

        self.llm_client = LLMClient(llm_config)

        # 传递 llm_client 给 ReActAgent，使其能使用 LLM 进行思考
        self.react_agent = ReActAgent(
            name="TravelReActAgent",
            max_steps=max_steps,
            max_reasoning_depth=5,
            llm_client=self.llm_client
        )

        self._register_tools()
        self._register_callbacks()

    def _register_tools(self) -> None:
        tools = create_travel_tools(self.config_manager)
        for tool_info, executor in tools:
            self.react_agent.register_tool(tool_info, executor)

    def _register_callbacks(self) -> None:
        def on_thought(thought: Thought):
            self.memory_manager.add_message('assistant', f"[思考] {thought.content}")

        def on_action(action: Action):
            if action.status == ActionStatus.RUNNING:
                self.memory_manager.add_message('assistant', f"[行动] 执行工具: {action.tool_name}")
            elif action.status == ActionStatus.SUCCESS:
                self.memory_manager.add_message('assistant', f"[完成] {action.tool_name}")
            elif action.status == ActionStatus.FAILED:
                self.memory_manager.add_message('assistant', f"[失败] {action.tool_name}: {action.error}")

        self.react_agent.add_thought_callback(on_thought)
        self.react_agent.add_action_callback(on_action)

    async def process(self, user_input: str) -> Dict[str, Any]:
        """处理用户输入"""
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"[Agent] 开始处理用户输入: {user_input[:50]}...")

        try:
            self.memory_manager.add_message('user', user_input)

            context = {
                'user_query': user_input,
                'user_preference': self.memory_manager.get_user_preference()
            }

            result = await self.react_agent.run(user_input, context)
            logger.info(f"[Agent] ReAct 执行完成, success={result.get('success')}, steps={len(result.get('history', []))}")

            if result.get('success'):
                history = result.get('history', [])
                reasoning_text = self._build_reasoning_text(history)
                answer = self._extract_answer(history)
                logger.info(f"[Agent] 提取到答案: {answer[:100]}...")

                self.memory_manager.add_message('assistant', answer)

                return {
                    "success": True,
                    "answer": answer,
                    "reasoning": {
                        "text": reasoning_text,
                        "total_steps": len(history),
                        "tools_used": self._extract_tools_used(history)
                    },
                    "history": history
                }
            else:
                return {
                    "success": False,
                    "error": result.get('error', '处理失败'),
                    "reasoning": None,
                    "history": result.get('history', [])
                }

        except Exception as e:
            logger.error(f"[Agent] 处理异常: {e}")
            return {
                "success": False,
                "error": f"处理失败: {str(e)}",
                "reasoning": None
            }

    def process_sync(self, user_input: str) -> Dict[str, Any]:
        """同步处理用户输入（用于 gRPC 调用）"""
        import asyncio
        return asyncio.run(self.process(user_input))

    def _build_reasoning_text(self, history: List[Dict]) -> str:
        if not history:
            return "<thinking>\n[Timestamp: {timestamp}]\n\n[Intent Analysis]\nNo reasoning history available.\n\n[Context Evaluation]\nNo context available.\n\n[Response Planning]\nUnable to generate response.\n\n[Constraint Check]\nNo constraints checked.\n</thinking>".format(
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )

        intent_analysis = []
        context_evaluation = []
        response_planning = []
        constraint_check = []

        for i, step in enumerate(history):
            thought = step.get('thought', {})
            action = step.get('action', {})

            thought_type = thought.get('type', 'UNKNOWN')
            thought_content = thought.get('content', '')
            action_name = action.get('tool_name', '')
            action_status = action.get('status', 'PENDING')
            result = action.get('result', {})

            if thought_type == 'ANALYSIS':
                if thought_content:
                    intent_analysis.append(f"Step {i + 1}: {thought_content}")
            elif thought_type == 'PLANNING':
                if thought_content:
                    response_planning.append(f"Step {i + 1}: {thought_content}")
            elif thought_type == 'INFERENCE':
                if thought_content:
                    context_evaluation.append(f"Step {i + 1}: {thought_content}")
                if action_name and action_name != 'none':
                    status_str = 'SUCCESS' if action_status == 'SUCCESS' else 'FAILED' if action_status == 'FAILED' else 'RUNNING'
                    context_evaluation.append(f"  - Tool: {action_name} [{status_str}]")
            elif thought_type == 'REFLECTION':
                if thought_content:
                    constraint_check.append(f"Step {i + 1}: {thought_content}")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        intent_section = "[Intent Analysis]\n"
        if intent_analysis:
            intent_section += "\n".join(intent_analysis)
        else:
            intent_section += f"User query analysis based on {len(history)} reasoning steps.\n"

        context_section = "[Context Evaluation]\n"
        if context_evaluation:
            context_section += "\n".join(context_evaluation)
        else:
            context_section += "No explicit context evaluation steps recorded."

        response_section = "[Response Planning]\n"
        if response_planning:
            response_section += "\n".join(response_planning)
        else:
            response_section += "Response generation based on tool execution results."

        constraint_section = "[Constraint Check]\n"
        if constraint_check:
            constraint_section += "\n".join(constraint_check)
        else:
            constraint_section += "All constraints satisfied.\n"
            constraint_section += f"- Total reasoning steps: {len(history)}\n"
            constraint_section += f"- Tools executed: {len(self._extract_tools_used(history))}\n"
            constraint_section += "- Response format: Standard text response"

        thinking_content = f"""[Timestamp: {timestamp}]

{intent_section}

{context_section}

{response_section}

{constraint_section}"""

        return f"<thinking>\n{thinking_content}\n</thinking>"

    def _extract_tools_used(self, history: List[Dict]) -> List[str]:
        tools = []
        for step in history:
            action = step.get('action', {})
            tool_name = action.get('tool_name', '')
            if tool_name and tool_name not in tools and tool_name != 'none':
                tools.append(tool_name)
        return tools

    def _extract_answer(self, history: List[Dict]) -> str:
        for step in reversed(history):
            action = step.get('action', {})
            if action.get('status') == 'SUCCESS':
                action_result = step.get('evaluation', {})
                result = action.get('result', {})
                tool_name = action.get('tool_name', '')

                # Handle all tools that return useful results
                if tool_name in ['generate_city_recommendation', 'generate_route_plan', 'llm_chat', 'query_attractions', 'generate_route']:
                    if result:
                        # Check for response/content fields
                        response = result.get('response') or result.get('content', '')
                        if response:
                            if isinstance(response, dict):
                                return json.dumps(response, ensure_ascii=False)
                            return str(response)

                        # For query_attractions, format the attractions data
                        if tool_name == 'query_attractions' and isinstance(result, dict):
                            # Check for data key (new format) or cities key (old format)
                            if result.get('data') or result.get('cities'):
                                return self._format_attractions_response(result)

                        # For generate_route, return the route plan
                        if tool_name == 'generate_route' and isinstance(result, dict):
                            route_plan = result.get('route_plan', [])
                            if route_plan:
                                return json.dumps(result, ensure_ascii=False)

                if action_result:
                    response = action_result.get('response') or action_result.get('content', '')
                    if response:
                        if isinstance(response, dict):
                            return json.dumps(response, ensure_ascii=False)
                        return str(response)

        return self._generate_answer(history)

    def _format_attractions_response(self, tool_result: Dict) -> str:
        """Format attractions data into a readable response."""
        lines = []

        # Handle both old format (cities key) and new format (data key)
        if 'cities' in tool_result:
            data = tool_result['cities']
        elif 'data' in tool_result:
            data = tool_result['data']
        else:
            data = tool_result

        if not data:
            return "未找到相关景点信息"

        for city, data_item in data.items():
            region = data_item.get('region', '') if isinstance(data_item, dict) else ''
            region_str = f" (来自{region}地区)" if region else ""
            lines.append(f"\n## {city}{region_str}")
            attractions = data_item.get('attractions', []) if isinstance(data_item, dict) else []
            if attractions:
                lines.append("\n### 景点推荐：")
                for i, attr in enumerate(attractions[:10], 1):
                    name = attr.get('name', '未知景点')
                    desc = attr.get('description', '')[:100]
                    ticket = attr.get('ticket', 0)
                    lines.append(f"{i}. **{name}**")
                    if desc:
                        lines.append(f"   - {desc}")
                    if ticket > 0:
                        lines.append(f"   - 门票: ¥{ticket}")
            else:
                lines.append("  暂无景点信息")

        return '\n'.join(lines) if lines else "未找到相关景点信息"

    def _generate_answer(self, history: List[Dict]) -> str:
        try:
            tool_results = []
            for step in history:
                action = step.get('action', {})
                if action.get('status') == 'SUCCESS' and action.get('result'):
                    tool_results.append({
                        'tool': action.get('tool_name', ''),
                        'result': action.get('result', {})
                    })

            system_prompt = """你是一个专业的AI旅游助手。请基于工具调用结果，为用户提供完整、详细、专业的回答。"""

            user_prompt = f"工具调用结果：\n{json.dumps(tool_results, ensure_ascii=False, indent=2)}\n\n请提供完整回答。"

            result = self.llm_client.chat([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ])

            if result.get('success'):
                return result.get('content', '处理完成')
            return '处理完成'

        except Exception as e:
            return f'生成回答失败：{str(e)}'

    def get_conversation_history(self) -> list:
        return self.memory_manager.get_conversation_history()

    def clear_conversation(self) -> None:
        self.memory_manager.clear_conversation()
        self.react_agent.reset()
