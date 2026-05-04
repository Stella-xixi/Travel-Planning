"""
ReAct 旅游助手 Agent
====================

基于 ReAct (Reasoning and Acting) 模式的旅游智能体实现。

核心架构：
- 观察（Observation）：感知用户输入和环境状态
- 思考（Thought）：推理分析、决策制定
- 行动（Action）：执行工具调用、数据查询
- 反馈（Feedback）：评估结果、反思调整

模块说明：
- 工具定义：封装旅游领域的功能为ReAct工具
- 工具执行函数：实现具体的业务逻辑
- ReActTravelAgent：整合ReAct引擎与旅游领域功能

版本：2.0.0
"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from .config_manager import ConfigManager
from .memory_manager import MemoryManager
from .llm_client import LLMClient
from .react_agent import (
    ReActAgent, ToolInfo, Action, Thought, Observation,
    AgentState, ActionStatus, ThoughtType
)
from .environment import Environment


# ==================== 工具定义 ====================

def create_travel_tools(config_manager: ConfigManager) -> List[tuple]:
    """
    创建旅游助手工具列表

    将环境模块中的功能封装为ReAct Agent可调用的工具。

    Args:
        config_manager: 配置管理器实例

    Returns:
        工具列表，每个元素为 (ToolInfo, 执行函数)
    """
    tools = []

    # ---- 搜索城市工具 ----
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
                        'description': '用户兴趣标签列表，如：历史文化、自然风光、美食等'
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

    # ---- 查询景点工具 ----
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

    # ---- 路线规划工具 ----
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

    # ---- 计算预算工具 ----
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

    # ---- 获取城市信息工具 ----
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

    # ---- LLM对话工具 ----
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

    # ---- 生成城市推荐工具 ----
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

    # ---- 生成路线规划工具 ----
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


# ==================== 工具执行函数 ====================

def _search_cities(config_manager, interests: List[str] = None,
                   budget: tuple = None, season: str = None) -> Dict[str, Any]:
    """搜索匹配城市"""
    env = Environment(config_manager)
    return env.search_cities(interests, budget, season)


def _query_attractions(config_manager, cities: List[str]) -> Dict[str, Any]:
    """查询景点信息"""
    env = Environment(config_manager)
    return env.query_attractions(cities)


def _generate_route(config_manager, city: str, days: int) -> Dict[str, Any]:
    """生成路线（简单版本）"""
    env = Environment(config_manager)
    result = env.get_city_info(city)
    if not result.get('success'):
        return result

    city_info = result.get('info', {})
    attractions = city_info.get('attractions', [])

    # 生成简单路线
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
    """计算预算"""
    env = Environment(config_manager)
    return env.calculate_budget(city, days)


def _get_city_info(config_manager, city: str) -> Dict[str, Any]:
    """获取城市信息"""
    env = Environment(config_manager)
    return env.get_city_info(city)


def _llm_chat(config_manager, query: str, context: str = "") -> Dict[str, Any]:
    """
    LLM对话

    Args:
        config_manager: 配置管理器
        query: 用户问题
        context: 对话上下文

    Returns:
        包含success和response字段的字典
    """
    llm_config = config_manager.get_llm_config()
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
    """生成城市推荐"""
    llm_config = config_manager.get_llm_config()
    llm_client = LLMClient(llm_config)
    return llm_client.generate_travel_recommendation(user_query, "", available_cities)


def _generate_route_plan(config_manager, city: str, days: int,
                         preferences: str = "") -> Dict[str, Any]:
    """生成路线规划"""
    city_info = config_manager.get_city_info(city)
    if not city_info:
        return {'success': False, 'error': f'未找到城市: {city}'}

    attractions = city_info.get('attractions', [])
    llm_config = config_manager.get_llm_config()
    llm_client = LLMClient(llm_config)
    return llm_client.generate_route_plan(city, days, attractions, preferences)


# ==================== ReAct 旅游助手 Agent ====================

class ReActTravelAgent:
    """
    ReAct 旅游助手 Agent

    基于ReAct模式的智能体，整合旅游领域的工具和推理能力。

    使用示例：
    ```python
    agent = ReActTravelAgent()
    result = agent.process("推荐一些适合亲子游的城市")
    ```

    Attributes:
        config_manager: 配置管理器
        memory_manager: 内存管理器
        llm_client: LLM客户端
        react_agent: ReAct引擎实例
    """

    def __init__(self, config_path: str = "config/config.json",
                 model_config: Optional[str] = None,
                 max_steps: int = 10):
        """
        初始化ReAct旅游助手

        Args:
            config_path: 配置文件路径
            model_config: 可选的模型ID
            max_steps: 最大推理步骤数
        """
        # 初始化配置管理
        self.config_manager = ConfigManager(config_path)

        # 初始化内存管理
        memory_config = self.config_manager.get_config('memory', {})
        self.memory_manager = MemoryManager(
            max_working_memory=memory_config.get('max_working_memory', 10)
        )

        # 初始化LLM客户端
        llm_config = self.config_manager.get_llm_config(model_config)
        self.llm_client = LLMClient(llm_config)

        # 初始化ReAct引擎
        self.react_agent = ReActAgent(
            name="TravelReActAgent",
            max_steps=max_steps,
            max_reasoning_depth=5
        )

        # 注册工具和回调
        self._register_tools()
        self._register_callbacks()

    def _register_tools(self) -> None:
        """注册旅游工具到ReAct引擎"""
        tools = create_travel_tools(self.config_manager)
        for tool_info, executor in tools:
            self.react_agent.register_tool(tool_info, executor)

    def _register_callbacks(self) -> None:
        """注册事件回调"""
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
        """
        处理用户输入

        执行ReAct循环，返回结构化响应。

        Args:
            user_input: 用户输入

        Returns:
            结构化处理结果，包含：
            - success: 是否成功
            - answer: 最终答案
            - reasoning: 思考过程
            - history: 完整执行历史
        """
        try:
            # 添加用户消息到记忆
            self.memory_manager.add_message('user', user_input)

            # 构建上下文
            context = {
                'user_query': user_input,
                'user_preference': self.memory_manager.get_user_preference()
            }

            # 执行ReAct循环（异步等待）
            result = await self.react_agent.run(user_input, context)

            if result.get('success'):
                history = result.get('history', [])
                reasoning_text = self._build_reasoning_text(history)
                answer = self._extract_answer(history)

                # 添加助手回复到记忆
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
            return {
                "success": False,
                "error": f"处理失败: {str(e)}",
                "reasoning": None
            }

    def _build_reasoning_text(self, history: List[Dict]) -> str:
        """
        构建人类可读的思考过程文本，完整展示agent的决策链条
        使用<thinking>标签包裹，英文书写

        Args:
            history: 执行历史

        Returns:
            格式化的思考过程文本（用<thinking>标签包裹）
        """
        if not history:
            return "<thinking>\n[Timestamp: {timestamp}]\n\n[Intent Analysis]\nNo reasoning history available.\n\n[Context Evaluation]\nNo context available.\n\n[Response Planning]\nUnable to generate response.\n\n[Constraint Check]\nNo constraints checked.\n</thinking>".format(
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )

        # 收集各个阶段的信息
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

            # 根据思考类型分类
            if thought_type == 'ANALYSIS':
                if thought_content:
                    intent_analysis.append(f"Step {i + 1}: {thought_content}")
            elif thought_type == 'PLANNING':
                if thought_content:
                    response_planning.append(f"Step {i + 1}: {thought_content}")
            elif thought_type == 'INFERENCE':
                if thought_content:
                    context_evaluation.append(f"Step {i + 1}: {thought_content}")
                # 收集工具调用信息
                if action_name and action_name != 'none':
                    status_str = 'SUCCESS' if action_status == 'SUCCESS' else 'FAILED' if action_status == 'FAILED' else 'RUNNING'
                    context_evaluation.append(f"  - Tool: {action_name} [{status_str}]")
                    if result and isinstance(result, dict):
                        if result.get('success'):
                            context_evaluation.append(f"  - Result: Tool executed successfully")
                        elif result.get('error'):
                            context_evaluation.append(f"  - Error: {result.get('error')}")
            elif thought_type == 'REFLECTION':
                if thought_content:
                    constraint_check.append(f"Step {i + 1}: {thought_content}")
                    # 检查置信度
                    confidence = thought.get('confidence', 0)
                    if confidence > 0:
                        constraint_check.append(f"  - Confidence: {confidence:.0%}")

        # 构建英文思考过程
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Intent Analysis
        intent_section = "[Intent Analysis]\n"
        if intent_analysis:
            intent_section += "\n".join(intent_analysis)
        else:
            intent_section += f"User query analysis based on {len(history)} reasoning steps.\n"
            # 从第一个思考中提取意图
            if history:
                first_thought = history[0].get('thought', {}).get('content', '')
                if first_thought:
                    intent_section += f"Initial analysis: {first_thought[:200]}"

        # Context Evaluation
        context_section = "[Context Evaluation]\n"
        if context_evaluation:
            context_section += "\n".join(context_evaluation)
        else:
            context_section += "No explicit context evaluation steps recorded."

        # Response Planning
        response_section = "[Response Planning]\n"
        if response_planning:
            response_section += "\n".join(response_planning)
        else:
            response_section += "Response generation based on tool execution results.\n"
            # 收集使用的工具
            tools_used = self._extract_tools_used(history)
            if tools_used:
                response_section += f"Tools to be used: {', '.join(tools_used)}"

        # Constraint Check
        constraint_section = "[Constraint Check]\n"
        if constraint_check:
            constraint_section += "\n".join(constraint_check)
        else:
            constraint_section += "All constraints satisfied.\n"
            constraint_section += f"- Total reasoning steps: {len(history)}\n"
            constraint_section += f"- Tools executed: {len(self._extract_tools_used(history))}\n"
            constraint_section += "- Response format: Standard text response"

        # 组合完整思考过程
        thinking_content = f"""[Timestamp: {timestamp}]

{intent_section}

{context_section}

{response_section}

{constraint_section}"""

        return f"<thinking>\n{thinking_content}\n</thinking>"

    def _extract_tools_used(self, history: List[Dict]) -> List[str]:
        """提取使用的工具列表"""
        tools = []
        for step in history:
            action = step.get('action', {})
            tool_name = action.get('tool_name', '')
            if tool_name and tool_name not in tools and tool_name != 'none':
                tools.append(tool_name)
        return tools

    def _extract_answer(self, history: List[Dict]) -> str:
        """从执行历史中提取最终答案"""
        for step in reversed(history):
            action = step.get('action', {})
            if action.get('status') == 'SUCCESS':
                action_result = step.get('evaluation', {})
                result = action.get('result', {})

                # 优先使用LLM相关工具的响应
                if action.get('tool_name') in ['generate_city_recommendation', 'generate_route_plan', 'llm_chat']:
                    if result:
                        response = result.get('response') or result.get('content', '')
                        if response:
                            # 确保返回字符串
                            if isinstance(response, dict):
                                return json.dumps(response, ensure_ascii=False)
                            return str(response)

                if action_result:
                    response = action_result.get('response') or action_result.get('content', '')
                    if response:
                        if isinstance(response, dict):
                            return json.dumps(response, ensure_ascii=False)
                        return str(response)

        # 如果没有找到答案，使用LLM生成
        return self._generate_answer(history)

    def _generate_answer(self, history: List[Dict]) -> str:
        """使用LLM生成最终答案"""
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
        """获取对话历史"""
        return self.memory_manager.get_conversation_history()

    def clear_conversation(self) -> None:
        """清空当前会话"""
        self.memory_manager.clear_conversation()
        self.react_agent.reset()
