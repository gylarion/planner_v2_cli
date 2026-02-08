from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from app.enums import Role, AccessMode, Permission
from app.models import (
    User,
    GuestSession,
    Planner,
    Member,
    Task,
    Invite,
    AccessRequest,
    LogEntry,
)


def _serialize(obj: Any) -> Any:
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, set):
        return list(obj)
    if is_dataclass(obj):
        return {k: _serialize(v) for k, v in asdict(obj).items()}
    if isinstance(obj, list):
        return [_serialize(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    return obj


def _dt(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


class DataStore:
    def __init__(self, path: str = "data/state.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

        if not self.path.exists():
            self._write(
                {
                    "users": [],
                    "guests": [],
                    "planners": [],
                    "tasks": [],
                    "invites": [],
                    "requests": [],
                    "logs": [],
                }
            )

    def _read(self) -> dict[str, Any]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, data: dict[str, Any]) -> None:
        self.path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def load(self) -> dict[str, Any]:
        raw = self._read()

        users = [User(**u) for u in raw["users"]]

        guests = [
            GuestSession(
                guest_id=g["guest_id"],
                user_name=g["username"],
                created_at=_dt(g["created_at"]),
            )
            for g in raw["guests"]
        ]

        planners: list[Planner] = []
        for p in raw["planners"]:
            members = [
                Member(
                    user_id=m["user_id"],
                    role=Role(m["role"]),
                    permissions={Permission(x) for x in m["permissions"]},
                )
                for m in p["members"]
            ]

            planners.append(
                Planner(
                    planner_id=p["planner_id"],
                    title=p["title"],
                    access_mode=AccessMode(p["access_mode"]),
                    created_at=_dt(p["created_at"]),
                    updated_at=_dt(p["updated_at"]),
                    is_guest=p["is_guest"],
                    expires_at=_dt(p["expires_at"]),
                    guest_id=p["guest_id"],
                    members=members,
                )
            )

        tasks = [
            Task(
                task_id=t["task_id"],
                planner_id=t["planner_id"],
                author_id=t["author_id"],
                text=t["text"],
                deadline=_dt(t["deadline"]),
                created_at=_dt(t["created_at"]),
                updated_at=_dt(t["updated_at"]),
            )
            for t in raw["tasks"]
        ]

        invites = [
            Invite(
                invite_code=i["invite_code"],
                planner_id=i["planner_id"],
                role=Role(i["role"]),
                permissions={Permission(x) for x in i["permissions"]},
                created_at=_dt(i["created_at"]),
                expires_at=_dt(i["expires_at"]),
                usage_limit=i["usage_limit"],
                used_count=i["used_count"],
            )
            for i in raw["invites"]
        ]

        requests = [
            AccessRequest(
                request_id=r["request_id"],
                planner_id=r["planner_id"],
                user_id=r["user_id"],
                created_at=_dt(r["created_at"]),
                status=r["status"],
            )
            for r in raw["requests"]
        ]

        logs = [
            LogEntry(
                log_id=l["log_id"],
                planner_id=l["planner_id"],
                actor_id=l["actor_id"],
                action=l["action"],
                created_at=_dt(l["created_at"]),
                details=l["details"],
            )
            for l in raw["logs"]
        ]

        return {
            "users": users,
            "guests": guests,
            "planners": planners,
            "tasks": tasks,
            "invites": invites,
            "requests": requests,
            "logs": logs,
        }

    def save(self, state: dict[str, Any]) -> None:
        self._write(
            {
                "users": [_serialize(u) for u in state["users"]],
                "guests": [_serialize(g) for g in state["guests"]],
                "planners": [_serialize(p) for p in state["planners"]],
                "tasks": [_serialize(t) for t in state["tasks"]],
                "invites": [_serialize(i) for i in state["invites"]],
                "requests": [_serialize(r) for r in state["requests"]],
                "logs": [_serialize(l) for l in state["logs"]],
            }
        )
