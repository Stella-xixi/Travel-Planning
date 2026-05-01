"""
多协议大模型调用模块 (Multi-Protocol LLM Client)

架构概述：
    本模块采用适配器模式和工厂模式，支持多种LLM API协议：
    - OpenAI API（官方）：gpt-4, gpt-4o, gpt-4o-mini等
    - Anthropic Claude API：claude-3-sonnet, claude-3-opus等
    - Google Gemini API：gemini-1.5-pro, gemini-1.5-flash等  
    - OpenAI-Compatible API：本地或第三方兼容OpenAI格式的API
    
核心类：
    - LLMProtocolAdapter：协议抽象基类，定义统一接口
    - OpenAIAdapter：OpenAI协议实现
    - AnthropicAdapter：Anthropic Claude API实现
    - GoogleAdapter：Google Gemini API实现
    - OpenAICompatibleAdapter：通用OpenAI兼容协议实现
    - LLMClientFactory：工厂类，动态选择协议实现
    - LLMClient：统一客户端，对外提供一致的调用接口

职责分工：
    1. 协议适配：封装各协议的请求/响应格式转换
    2. 错误处理：统一的重试机制、超时处理、错误恢复
    3. 流式处理：支持SSE流式输出，统一解析各协议的流数据
    4. 参数映射：将通用参数映射到协议特定的参数
    5. 工厂选择：根据配置自动选择合适的协议实现
"""

import json
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Iterator
import urllib.request
import urllib.error
from enum import Enum


class ProtocolType(Enum):
    """支持的LLM协议类型"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OPENAI_COMPATIBLE = "openai-compatible"


class LLMProtocolAdapter(ABC):
    """
    LLM协议适配器抽象基类
    
    定义统一的接口，由具体协议实现类继承和实现。
    确保不同协议的API调用在外部呈现一致的接口。
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化协议适配器
        
        Args:
            config: 协议特定的配置字典
        """
        self.api_key = config.get('api_key', '')
        self.model = config.get('model', '')
        self.api_base = config.get('api_base', '')
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 2000)
        self.timeout = config.get('timeout', 30)
        self.max_retries = config.get('max_retries', 3)
        self.top_p = config.get('top_p', 1.0)
        self.frequency_penalty = config.get('frequency_penalty', 0.0)
        self.presence_penalty = config.get('presence_penalty', 0.0)
        
        # 协议特定的参数（子类可覆盖）
        self._init_protocol_specific(config)
    
    @abstractmethod
    def _init_protocol_specific(self, config: Dict[str, Any]):
        """初始化协议特定的参数，由子类实现"""
        pass
    
    @abstractmethod
    def _build_request_payload(self, messages: List[Dict[str, str]], 
                               temperature: Optional[float] = None,
                               max_tokens: Optional[int] = None,
                               stream: bool = False) -> Dict[str, Any]:
        """构建协议特定的请求载荷"""
        pass
    
    @abstractmethod
    def _build_request_headers(self) -> Dict[str, str]:
        """构建协议特定的请求头"""
        pass
    
    @abstractmethod
    def _get_chat_endpoint(self) -> str:
        """获取协议特定的聊天端点"""
        pass
    
    @abstractmethod
    def _parse_stream_chunk(self, line: str) -> Optional[str]:
        """解析流式响应的单行数据"""
        pass
    
    @abstractmethod
    def _parse_response(self, response_data: Dict[str, Any]) -> str:
        """解析API响应，提取文本内容"""
        pass
    
    def chat_stream(self, messages: List[Dict[str, str]], 
                    temperature: Optional[float] = None,
                    max_tokens: Optional[int] = None) -> Iterator[str]:
        """流式调用API（通用实现）"""
        payload = self._build_request_payload(messages, temperature, max_tokens, stream=True)
        headers = self._build_request_headers()
        endpoint = self._get_chat_endpoint()
        
        try:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(endpoint, data=data, headers=headers, method='POST')
            
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                for line in response:
                    line = line.decode('utf-8').strip()
                    if not line:
                        continue
                    content = self._parse_stream_chunk(line)
                    if content:
                        yield content
        
        except urllib.error.HTTPError as e:
            error_msg = e.read().decode('utf-8')
            yield f"\n\n[错误: HTTP {e.code} - {error_msg}]\n"
        except urllib.error.URLError as e:
            yield f"\n\n[错误: 网络连接失败 - {str(e.reason)}]\n"
        except Exception as e:
            yield f"\n\n[错误: {str(e)}]\n"
    
    def chat(self, messages: List[Dict[str, str]], 
             temperature: Optional[float] = None,
             max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """非流式调用API（通用实现，带重试）"""
        payload = self._build_request_payload(messages, temperature, max_tokens, stream=False)
        headers = self._build_request_headers()
        endpoint = self._get_chat_endpoint()
        
        # 重试逻辑（指数退避）
        for attempt in range(self.max_retries):
            try:
                data = json.dumps(payload).encode('utf-8')
                req = urllib.request.Request(endpoint, data=data, headers=headers, method='POST')
                
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    response_data = json.loads(response.read().decode('utf-8'))
                    content = self._parse_response(response_data)
                    
                    return {
                        "success": True,
                        "content": content,
                        "usage": response_data.get('usage', {}),
                        "model": response_data.get('model', self.model)
                    }
            
            except urllib.error.HTTPError as e:
                error_msg = e.read().decode('utf-8')
                print(f"HTTP错误 (尝试 {attempt + 1}/{self.max_retries}): {e.code} - {error_msg}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    return {"success": False, "error": f"HTTP {e.code}: {error_msg}"}
            
            except urllib.error.URLError as e:
                print(f"网络错误 (尝试 {attempt + 1}/{self.max_retries}): {str(e.reason)}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    return {"success": False, "error": f"网络错误: {str(e.reason)}"}
            
            except Exception as e:
                print(f"未知错误 (尝试 {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    return {"success": False, "error": f"未知错误: {str(e)}"}
        
        return {"success": False, "error": "超过最大重试次数"}


class OpenAIAdapter(LLMProtocolAdapter):
    """OpenAI API协议适配器"""
    
    def _init_protocol_specific(self, config: Dict[str, Any]):
        if not self.api_base:
            self.api_base = "https://api.openai.com/v1"
    
    def _build_request_payload(self, messages: List[Dict[str, str]], 
                               temperature: Optional[float] = None,
                               max_tokens: Optional[int] = None,
                               stream: bool = False) -> Dict[str, Any]:
        return {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "stream": stream
        }
    
    def _build_request_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def _get_chat_endpoint(self) -> str:
        return f"{self.api_base.rstrip('/')}/chat/completions"
    
    def _parse_stream_chunk(self, line: str) -> Optional[str]:
        if not line.startswith('data: '):
            return None
        data_str = line[6:].strip()
        if data_str == '[DONE]':
            return None
        try:
            chunk = json.loads(data_str)
            delta = chunk.get('choices', [{}])[0].get('delta', {})
            content = delta.get('content', '')
            return content if content else None
        except json.JSONDecodeError:
            return None
    
    def _parse_response(self, response_data: Dict[str, Any]) -> str:
        return response_data['choices'][0]['message']['content']


class AnthropicAdapter(LLMProtocolAdapter):
    """Anthropic Claude API协议适配器"""
    
    def _init_protocol_specific(self, config: Dict[str, Any]):
        if not self.api_base:
            self.api_base = "https://api.anthropic.com/v1"
        self.api_version = config.get('api_version', '2023-06-01')
    
    def _build_request_payload(self, messages: List[Dict[str, str]], 
                               temperature: Optional[float] = None,
                               max_tokens: Optional[int] = None,
                               stream: bool = False) -> Dict[str, Any]:
        # Anthropic分离system消息
        system_message = None
        other_messages = []
        for msg in messages:
            if msg.get('role') == 'system':
                system_message = msg.get('content', '')
            else:
                other_messages.append(msg)
        
        payload = {
            "model": self.model,
            "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
            "temperature": temperature if temperature is not None else self.temperature,
            "messages": other_messages,
            "stream": stream
        }
        if system_message:
            payload["system"] = system_message
        return payload
    
    def _build_request_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": self.api_version
        }
    
    def _get_chat_endpoint(self) -> str:
        return f"{self.api_base.rstrip('/')}/messages"
    
    def _parse_stream_chunk(self, line: str) -> Optional[str]:
        if not line.startswith('data: '):
            return None
        data_str = line[6:].strip()
        try:
            chunk = json.loads(data_str)
            if chunk.get('type') == 'content_block_delta':
                delta = chunk.get('delta', {})
                if delta.get('type') == 'text_delta':
                    return delta.get('text', '')
        except json.JSONDecodeError:
            pass
        return None
    
    def _parse_response(self, response_data: Dict[str, Any]) -> str:
        content_blocks = response_data.get('content', [])
        text_content = [block.get('text', '') for block in content_blocks if block.get('type') == 'text']
        return ''.join(text_content)


class GoogleAdapter(LLMProtocolAdapter):
    """Google Gemini API协议适配器（OpenAI兼容端点）"""
    
    def _init_protocol_specific(self, config: Dict[str, Any]):
        if not self.api_base:
            self.api_base = "https://generativelanguage.googleapis.com/v1beta/openai"
    
    def _build_request_payload(self, messages: List[Dict[str, str]], 
                               temperature: Optional[float] = None,
                               max_tokens: Optional[int] = None,
                               stream: bool = False) -> Dict[str, Any]:
        return {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
            "top_p": self.top_p,
            "stream": stream
        }
    
    def _build_request_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def _get_chat_endpoint(self) -> str:
        return f"{self.api_base.rstrip('/')}/chat/completions"
    
    def _parse_stream_chunk(self, line: str) -> Optional[str]:
        if not line.startswith('data: '):
            return None
        data_str = line[6:].strip()
        if data_str == '[DONE]':
            return None
        try:
            chunk = json.loads(data_str)
            delta = chunk.get('choices', [{}])[0].get('delta', {})
            content = delta.get('content', '')
            return content if content else None
        except json.JSONDecodeError:
            return None
    
    def _parse_response(self, response_data: Dict[str, Any]) -> str:
        return response_data['choices'][0]['message']['content']


class OpenAICompatibleAdapter(LLMProtocolAdapter):
    """通用OpenAI兼容协议适配器（本地模型、Ollama等）"""
    
    def _init_protocol_specific(self, config: Dict[str, Any]):
        if not self.api_base:
            raise ValueError("OpenAI兼容协议必须提供api_base参数")
    
    def _build_request_payload(self, messages: List[Dict[str, str]], 
                               temperature: Optional[float] = None,
                               max_tokens: Optional[int] = None,
                               stream: bool = False) -> Dict[str, Any]:
        return {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
            "top_p": self.top_p,
            "stream": stream
        }
    
    def _build_request_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    def _get_chat_endpoint(self) -> str:
        return f"{self.api_base.rstrip('/')}/chat/completions"
    
    def _parse_stream_chunk(self, line: str) -> Optional[str]:
        if not line.startswith('data: '):
            return None
        data_str = line[6:].strip()
        if data_str == '[DONE]':
            return None
        try:
            chunk = json.loads(data_str)
            delta = chunk.get('choices', [{}])[0].get('delta', {})
            content = delta.get('content', '')
            return content if content else None
        except json.JSONDecodeError:
            return None
    
    def _parse_response(self, response_data: Dict[str, Any]) -> str:
        return response_data['choices'][0]['message']['content']


class LLMClientFactory:
    """LLM客户端工厂：根据配置动态创建协议适配器"""
    
    _ADAPTERS = {
        ProtocolType.OPENAI.value: OpenAIAdapter,
        ProtocolType.ANTHROPIC.value: AnthropicAdapter,
        ProtocolType.GOOGLE.value: GoogleAdapter,
        ProtocolType.OPENAI_COMPATIBLE.value: OpenAICompatibleAdapter,
    }
    
    @staticmethod
    def create_adapter(config: Dict[str, Any]) -> LLMProtocolAdapter:
        """
        创建LLM协议适配器
        
        Args:
            config: 配置字典，包含provider_type（可选，默认openai）等字段
                
        Returns:
            具体的协议适配器实例
        """
        # 向后兼容：未指定provider_type时默认使用OpenAI
        provider_type = config.get('provider_type', ProtocolType.OPENAI.value)
        provider_type = provider_type.lower()
        
        if provider_type not in LLMClientFactory._ADAPTERS:
            raise ValueError(
                f"不支持的协议类型: {provider_type}\n"
                f"支持的类型: {', '.join(LLMClientFactory._ADAPTERS.keys())}"
            )
        
        adapter_class = LLMClientFactory._ADAPTERS[provider_type]
        return adapter_class(config)
    
    @staticmethod
    def get_supported_protocols() -> List[str]:
        """获取支持的所有协议类型"""
        return list(LLMClientFactory._ADAPTERS.keys())


class LLMClient:
    """
    统一的LLM客户端
    
    为外部代码提供一致的调用接口，隐藏协议适配器的复杂性。
    支持所有协议的流式和非流式调用，以及高级功能（推荐、路线规划等）。
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化LLM客户端
        
        Args:
            config: LLM配置字典，包含provider_type（可选）和其他协议特定参数
        """
        # 使用工厂创建协议适配器
        self.adapter = LLMClientFactory.create_adapter(config)
        self.config = config
    
    def chat_stream(self, messages: List[Dict[str, str]], 
                    temperature: Optional[float] = None,
                    max_tokens: Optional[int] = None) -> Iterator[str]:
        """流式调用Chat API（SSE模式）"""
        return self.adapter.chat_stream(messages, temperature, max_tokens)
    
    def chat(self, messages: List[Dict[str, str]], 
             temperature: Optional[float] = None,
             max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """调用Chat API（非流式）"""
        return self.adapter.chat(messages, temperature, max_tokens)
    
    def generate_travel_recommendation(self, user_query: str, 
                                       context: str,
                                       available_cities: List[str]) -> Dict[str, Any]:
        """生成旅游推荐（城市推荐）"""
        system_prompt = f"""你是一个专业的旅游助手，负责根据用户需求推荐合适的旅游城市。

可推荐城市列表：{', '.join(available_cities)}

当前用户偏好：
{context}

请基于用户需求，从可推荐城市中选择3-5个最合适的城市，并以JSON格式返回：
{{
    "recommendations": [
        {{
            "city": "城市名",
            "reason": "推荐理由（50字以内）",
            "match_score": 90
        }}
    ],
    "explanation": "整体推荐说明（100字以内）"
}}

注意：
1. 只推荐列表中存在的城市
2. match_score为匹配度评分（0-100）
3. 推荐理由需结合用户偏好和城市特色
4. 按匹配度从高到低排序"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]
        
        response = self.chat(messages, temperature=0.7)
        
        if not response['success']:
            return response
        
        # 解析JSON响应
        try:
            content = response['content']
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            recommendations = json.loads(content)
            response['recommendations'] = recommendations
            return response
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"JSON解析失败: {str(e)}",
                "raw_content": response['content']
            }
    
    def generate_route_plan(self, city: str, 
                           days: int,
                           attractions: List[Dict[str, Any]],
                           user_preference: str) -> Dict[str, Any]:
        """生成旅游路线规划"""
        attractions_info = "\n".join([
            f"- {a['name']}：{a['type']}，建议游玩{a['duration']}小时，门票{a['ticket']}元"
            for a in attractions
        ])
        
        system_prompt = f"""你是一个专业的旅游规划师，负责为用户制定详细的旅游路线。

目标城市：{city}
旅行天数：{days}天
可选景点：
{attractions_info}

用户偏好：
{user_preference}

请制定一个{days}天的详细旅游路线，以JSON格式返回：
{{
    "route_plan": [
        {{
            "day": 1,
            "attractions": ["景点1", "景点2"],
            "schedule": "上午游览景点1（3小时），下午游览景点2（4小时）",
            "tips": "建议事项"
        }}
    ],
    "total_cost_estimate": {{
        "tickets": 500,
        "meals": 300,
        "transportation": 200,
        "total": 1000
    }},
    "travel_tips": ["tip1", "tip2", "tip3"]
}}

注意：
1. 合理安排每天行程，避免过于紧凑
2. 考虑景点间的地理位置和交通时间
3. 提供实用的旅行建议
4. 估算各项费用"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"帮我规划{city}{days}天的旅游路线"}
        ]
        
        response = self.chat(messages, temperature=0.6)
        
        if not response['success']:
            return response
        
        # 解析JSON响应
        try:
            content = response['content']
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            route_plan = json.loads(content)
            response['route_plan'] = route_plan
            return response
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"JSON解析失败: {str(e)}",
                "raw_content": response['content']
            }
    
    def chat_with_context(self, conversation_history: List[Dict[str, str]],
                          system_context: str) -> Dict[str, Any]:
        """带上下文的对话"""
        messages = [
            {"role": "system", "content": f"""你是一个专业的旅游助手，负责回答用户关于旅游的各类问题。

当前上下文：
{system_context}

请友好、专业地回答用户问题，提供实用的旅游建议。"""}
        ]
        
        messages.extend(conversation_history)
        
        return self.chat(messages)
