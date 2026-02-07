from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Set, List

from app.enums import Role, AccessMode, Permission

@dataclass(frozen=True)
class User:
    user_id: str
    email: Optional[str]
    name: str

@dataclass(frozen=True)
class GuestSession:
    guest_id: str
    user_name: str
    created_at: datetime

@dataclass(frozen=True)
class Member:
    user_id: str
    role: Role
    permissions: Set[Permission]

@dataclass
class Planner:
    planner_id: str
    title: str
    access_mode: AccessMode
    created_at: datetime
    updated_at: datetime
    is_guest: bool
    expires_at: Optional[datetime]
    guest_id: Optional[str]
    members: List[Member] = field(default_factory=list)

@dataclass
class Task:
    task_id: str
    planner_id: str
    author_id: str
    text: str
    date: datetime
    deadline: Optional[str]
    created_at: datetime
    updated_at: datetime

@dataclass(frozen=True)
class Invite:
    invite_code: str
    planner_id: str
    role: Role
    permissions: Set[Permission]
    created_at: datetime
    expires_at: Optional[datetime]
    usage_limit: Optional[int]
    used_count: int

@dataclass(frozen=True)
class AccessRequest:
    request_id: str
    planner_id: str
    user_id: str
    created_at: datetime
    status: str

@dataclass(frozen=True)
class LogEntry:
    log_id: str
    planner_id: str
    actor_id: str
    action: str
    created_at: datetime
    details: str