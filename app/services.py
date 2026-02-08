from __future__ import annotations

from datetime import timedelta
from typing import Optional

from app.access import (
    can_manage_members,
    can_edit_task,
    get_member,
    is_owner_or_admin,
)
from app.enums import Role, AccessMode, Permission
from app.models import (
    Planner,
    Member,
    Task,
    Invite,
    AccessRequest,
    LogEntry,
    User,
    GuestSession,
)
from app.utils import new_id, now


class ServiceError(Exception):
    pass


def log_action(state, planner_id: str, actor_id: str, action: str, details: str) -> None:
    state["logs"].append(
        LogEntry(
            log_id=new_id("log"),
            planner_id=planner_id,
            actor_id=actor_id,
            action=action,
            created_at=now(),
            details=details,
        )
    )


def ensure_user(state, user_id: str) -> None:
    if not any(u.user_id == user_id for u in state["users"]):
        raise ServiceError("User not found")


def create_user(state, name: str, email: Optional[str]) -> User:
    user = User(user_id=new_id("user"), name=name, email=email)
    state["users"].append(user)
    return user


def create_guest(state, username: str) -> GuestSession:
    guest = GuestSession(guest_id=new_id("guest"), user_name=username, created_at=now())
    state["guests"].append(guest)
    return guest


def create_planner(
    state,
    title: str,
    access_mode: AccessMode,
    owner_id: str,
    is_guest: bool,
    guest_id: Optional[str],
) -> Planner:
    ensure_user(state, owner_id)

    created = now()
    expires = created + timedelta(days=5) if is_guest else None

    owner = Member(
        user_id=owner_id,
        role=Role.OWNER,
        permissions={
            Permission.EDIT_ALL_TASKS,
            Permission.MANAGE_MEMBERS,
            Permission.MANAGE_SETTINGS,
            Permission.VIEW_LOGS,
        },
    )

    planner = Planner(
        planner_id=new_id("planner"),
        title=title,
        access_mode=access_mode,
        created_at=created,
        updated_at=created,
        is_guest=is_guest,
        expires_at=expires,
        guest_id=guest_id,
        members=[owner],
    )

    state["planners"].append(planner)
    log_action(state, planner.planner_id, owner_id, "PLANNER_CREATED", title)
    return planner


def add_task(
    state,
    planner_id: str,
    actor_id: str,
    text: str,
    deadline: Optional[str],
) -> Task:
    planner = next((p for p in state["planners"] if p.planner_id == planner_id), None)
    if not planner:
        raise ServiceError("Planner not found")

    if not get_member(planner, actor_id):
        raise ServiceError("Not a member")

    dl = None
    if deadline:
        from datetime import datetime
        dl = datetime.fromisoformat(deadline)

    task = Task(
        task_id=new_id("task"),
        planner_id=planner_id,
        author_id=actor_id,
        text=text,
        deadline=dl,
        created_at=now(),
        updated_at=now(),
    )

    state["tasks"].append(task)
    planner.updated_at = now()
    log_action(state, planner_id, actor_id, "TASK_CREATED", text)
    return task

def create_invite(
    state,
    planner_id: str,
    issuer_id: str,
    role: Role,
    expires_at: Optional[str] = None,
    usage_limit: Optional[int] = None,
) -> Invite:
    planner = next((p for p in state["planners"] if p.planner_id == planner_id), None)
    if not planner:
        raise ServiceError("Planner not found")

    if not can_manage_members(planner, issuer_id):
        raise ServiceError("Not allowed to create invite")

    if role == Role.OWNER:
        raise ServiceError("Cannot invite OWNER")

    if expires_at:
        from datetime import datetime
        exp = datetime.fromisoformat(expires_at)
        if exp <= now():
            raise ServiceError("Invite already expired")
    else:
        exp = None

    if usage_limit is not None and usage_limit <= 0:
        raise ServiceError("Invalid usage limit")

    if role == Role.ADMIN:
        permissions = {
            Permission.EDIT_ALL_TASKS,
            Permission.MANAGE_MEMBERS,
            Permission.VIEW_LOGS,
        }
    elif role == Role.MEMBER:
        permissions = {Permission.EDIT_OWN_TASKS}
    else:  # GUEST_MEMBER
        permissions = set()

    invite = Invite(
        invite_code=new_id("invite"),
        planner_id=planner_id,
        role=role,
        permissions=permissions,
        created_at=now(),
        expires_at=exp,
        usage_limit=usage_limit,
        used_count=0,
    )

    state["invites"].append(invite)
    log_action(
        state,
        planner_id,
        issuer_id,
        "INVITE_CREATED",
        f"role={role}",
    )

    return invite

