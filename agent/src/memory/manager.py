"""
记忆/状态管理模块 (Memory Manager)
"""

import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import deque


class Message:
    """对话消息"""

    def __init__(self, role: str, content: str, timestamp: Optional[str] = None):
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.now().isoformat()

    def to_dict(self) -> Dict[str, str]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'Message':
        return cls(data['role'], data['content'], data.get('timestamp'))


class UserPreference:
    """用户偏好"""

    def __init__(self):
        self.budget_range: Optional[tuple] = None
        self.travel_days: Optional[int] = None
        self.interest_tags: List[str] = []
        self.preferred_cities: List[str] = []
        self.season_preference: Optional[str] = None
        self.travel_companions: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "budget_range": self.budget_range,
            "travel_days": self.travel_days,
            "interest_tags": self.interest_tags,
            "preferred_cities": self.preferred_cities,
            "season_preference": self.season_preference,
            "travel_companions": self.travel_companions
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        self.budget_range = tuple(data['budget_range']) if data.get('budget_range') else None
        self.travel_days = data.get('travel_days')
        self.interest_tags = data.get('interest_tags', [])
        self.preferred_cities = data.get('preferred_cities', [])
        self.season_preference = data.get('season_preference')
        self.travel_companions = data.get('travel_companions')

    def update_from_text(self, text: str) -> None:
        text_lower = text.lower()

        if '预算' in text or '元' in text or '块' in text:
            import re
            numbers = re.findall(r'\d+', text)
            if numbers:
                nums = [int(n) for n in numbers]
                if len(nums) >= 2:
                    self.budget_range = (min(nums), max(nums))
                elif len(nums) == 1:
                    self.budget_range = (0, nums[0])

        if '天' in text:
            import re
            match = re.search(r'(\d+)\s*天', text)
            if match:
                self.travel_days = int(match.group(1))

        interest_keywords = {
            '历史': '历史文化',
            '文化': '历史文化',
            '自然': '自然风光',
            '风景': '自然风光',
            '美食': '美食',
            '海边': '海滨度假',
            '海滨': '海滨度假',
            '购物': '现代都市',
            '休闲': '休闲养生'
        }
        for keyword, tag in interest_keywords.items():
            if keyword in text and tag not in self.interest_tags:
                self.interest_tags.append(tag)


class MemoryManager:
    """记忆管理器"""

    def __init__(self, max_working_memory: int = 10, max_long_term_memory: int = 50):
        self.max_working_memory = max_working_memory
        self.max_long_term_memory = max_long_term_memory

        self.conversation_history: deque = deque(maxlen=max_working_memory)

        self.user_preference = UserPreference()

        self.session_state: Dict[str, Any] = {
            "session_id": f"session_{int(time.time())}",
            "start_time": datetime.now().isoformat(),
            "last_recommended_cities": [],
            "last_recommended_attractions": [],
            "current_plan": None
        }

        self.long_term_memory: List[Dict[str, Any]] = []

    def add_message(self, role: str, content: str) -> None:
        message = Message(role, content)
        self.conversation_history.append(message)

        if role == 'user':
            self.user_preference.update_from_text(content)

    def get_conversation_history(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        history = list(self.conversation_history)
        if limit:
            history = history[-limit:]
        return [msg.to_dict() for msg in history]

    def get_messages_for_llm(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        history = self.get_conversation_history(limit)
        return [{"role": msg['role'], "content": msg['content']} for msg in history]

    def update_session_state(self, key: str, value: Any) -> None:
        self.session_state[key] = value

    def get_session_state(self, key: str, default: Any = None) -> Any:
        return self.session_state.get(key, default)

    def clear_conversation(self, archive: bool = True) -> None:
        if archive:
            self._archive_session()

        self.conversation_history.clear()
        self.session_state['session_id'] = f"session_{int(time.time())}"
        self.session_state['start_time'] = datetime.now().isoformat()

    def _archive_session(self) -> None:
        messages = self.get_conversation_history()
        session_state = self.session_state.copy()
        user_preference = self.user_preference.to_dict()

        summary = self._generate_session_summary(messages, session_state)

        archive_record = {
            'session_id': session_state.get('session_id'),
            'start_time': session_state.get('start_time'),
            'end_time': datetime.now().isoformat(),
            'message_count': len(messages),
            'summary': summary,
            'user_preference': user_preference,
            'session_state': {
                'last_recommended_cities': session_state.get('last_recommended_cities', []),
                'last_recommended_attractions': session_state.get('last_recommended_attractions', []),
                'current_plan': session_state.get('current_plan')
            },
            'messages': messages
        }

        self.long_term_memory.append(archive_record)

        while len(self.long_term_memory) > self.max_long_term_memory:
            self.long_term_memory.pop(0)

    def _generate_session_summary(self, messages: List[Dict], session_state: Dict) -> str:
        summary_parts = []

        user_messages = [m for m in messages if m.get('role') == 'user']
        if user_messages:
            summary_parts.append(f"用户消息数: {len(user_messages)}")

        recommended_cities = session_state.get('last_recommended_cities', [])
        if recommended_cities:
            summary_parts.append(f"推荐城市: {', '.join(recommended_cities[:5])}")

        current_plan = session_state.get('current_plan')
        if current_plan:
            route_plan = current_plan.get('route_plan', [])
            if route_plan:
                summary_parts.append(f"已规划路线")

        return " | ".join(summary_parts) if summary_parts else "一般对话"

    def archive_current_session(self) -> Dict[str, Any]:
        self._archive_session()
        return self.long_term_memory[-1] if self.long_term_memory else {}

    def get_archived_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        archives = []
        for record in reversed(self.long_term_memory[-limit:]):
            archives.append({
                'session_id': record['session_id'],
                'start_time': record['start_time'],
                'end_time': record['end_time'],
                'message_count': record['message_count'],
                'summary': record['summary']
            })
        return archives

    def get_archive_detail(self, session_id: str) -> Optional[Dict[str, Any]]:
        for record in self.long_term_memory:
            if record['session_id'] == session_id:
                return record
        return None

    def get_long_term_memory(self) -> List[Dict[str, Any]]:
        return self.long_term_memory

    def set_long_term_memory(self, memory: List[Dict[str, Any]]) -> None:
        self.long_term_memory = memory[-self.max_long_term_memory:]

    def get_user_preference(self) -> Dict[str, Any]:
        return self.user_preference.to_dict()

    def set_user_preference(self, preference_data: Dict[str, Any]) -> None:
        self.user_preference.from_dict(preference_data)

    def save_to_file(self, filepath: str) -> None:
        data = {
            "session_state": self.session_state,
            "conversation_history": self.get_conversation_history(),
            "user_preference": self.user_preference.to_dict(),
            "long_term_memory": self.long_term_memory
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_from_file(self, filepath: str) -> bool:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.session_state = data.get('session_state', {})

            self.conversation_history.clear()
            for msg_data in data.get('conversation_history', []):
                msg = Message.from_dict(msg_data)
                self.conversation_history.append(msg)

            self.user_preference.from_dict(data.get('user_preference', {}))

            self.long_term_memory = data.get('long_term_memory', [])

            return True
        except Exception as e:
            print(f"加载记忆失败: {e}")
            return False

    def get_context_summary(self) -> str:
        summary_parts = []

        pref = self.user_preference
        if pref.budget_range:
            summary_parts.append(f"预算范围：{pref.budget_range[0]}-{pref.budget_range[1]}元/天")
        if pref.travel_days:
            summary_parts.append(f"旅行天数：{pref.travel_days}天")
        if pref.interest_tags:
            summary_parts.append(f"兴趣偏好：{', '.join(pref.interest_tags)}")
        if pref.preferred_cities:
            summary_parts.append(f"偏好城市：{', '.join(pref.preferred_cities)}")

        if self.session_state.get('last_recommended_cities'):
            summary_parts.append(f"已推荐城市：{', '.join(self.session_state['last_recommended_cities'])}")

        return "\n".join(summary_parts) if summary_parts else "暂无用户偏好信息"
