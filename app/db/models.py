from dataclasses import dataclass
from enum import Enum


class Role(str, Enum):
    user = "user"
    assistant = "assistant"


'''
uuid for when the chat starts, and which users, created when and updated when
This is for single convo thread and finn ai can look up at the chat's history
'''
@dataclass
class Session:
    session_id: str
    user_id: str
    created_at: float
    updated_at: float


'''
Storing each and every message of a session
NOTE: Role is between user or assistant
'''
@dataclass
class Message:
    id: int | None
    session_id: str
    role: Role
    content: str
    created_at: float
