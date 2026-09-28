from collections import defaultdict, deque
from typing import Deque, Dict, List


class ConversationStore:
    def __init__(self, max_messages: int = 12):
        self.max_messages = max_messages
        self._data: Dict[int, Deque[dict]] = defaultdict(lambda: deque(maxlen=self.max_messages))

    def get(self, user_id: int) -> List[dict]:
        return list(self._data[user_id])

    def append(self, user_id: int, role: str, content: str) -> None:
        self._data[user_id].append({"role": role, "content": content})

    def clear(self, user_id: int) -> None:
        self._data.pop(user_id, None)
