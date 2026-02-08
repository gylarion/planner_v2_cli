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

def _validate_invite(invite: Invite) -> None:
    if invite.expires_at and now() > invite.expires_at:
        raise ServiceError("Invite expired")

    if invite.usage_limit is not None and invite.used_count >= invite.usage_limit:
        raise ServiceError("Invite usage limit reached")

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
    else:
        permissions = set()

    invite = Invite(
        invite_code=new_id("inv"),
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
        f"role={role.value}",
    )

    return invite

def accept_invite(state, invite_code: str, user_id: str) -> None:
    ensure_user(state, user_id)

    invite = next((i for i in state["invites"] if i.invite_code == invite_code), None)
    if not invite:
        raise ServiceError("Invite not found")

    _validate_invite(invite)

    planner = next((p for p in state["planners"] if p.planner_id == invite.planner_id), None)
    if not planner:
        raise ServiceError("Planner not found")

    if get_member(planner, user_id):
        raise ServiceError("User already a member")

    planner.members.append(
        Member(
            user_id=user_id,
            role=invite.role,
            permissions=set(invite.permissions),
        )
    )

    invite.used_count += 1
    planner.updated_at = now()

    log_action(
        state,
        planner.planner_id,
        user_id,
        "INVITE_ACCEPTED",
        f"code={invite_code}",
    )

def request_access(state, planner_id: str, user_id: str) -> AccessRequest:
    ensure_user(state, user_id)

    planner = next((p for p in state["planners"] if p.planner_id == planner_id), None)
    if not planner:
        raise ServiceError("Planner not found")

    if planner.access_mode != AccessMode.REQUEST:
        raise ServiceError("Planner does not accept access requests")

    if get_member(planner, user_id):
        raise ServiceError("Already a member")

    existing = next(
        (
            r for r in state["requests"]
            if r.planner_id == planner_id
            and r.user_id == user_id
            and r.status == "PENDING"
        ),
        None,
    )
    if existing:
        return existing

    req = AccessRequest(
        request_id=new_id("req"),
        planner_id=planner_id,
        user_id=user_id,
        created_at=now(),
        status="PENDING",
    )

    state["requests"].append(req)
    log_action(
        state,
        planner_id,
        user_id,
        "ACCESS_REQUESTED",
        f"id={req.request_id}",
    )
    return req

def approve_request(
    state,
    request_id: str,
    actor_id: str,
    role: Role,
    permissions: set[Permission],
) -> None:
    req = next((r for r in state["requests"] if r.request_id == request_id), None)
    if not req:
        raise ServiceError("Request not found")

    planner = next((p for p in state["planners"] if p.planner_id == req.planner_id), None)
    if not planner:
        raise ServiceError("Planner not found")

    if not is_owner_or_admin(planner, actor_id):
        raise ServiceError("No permission to approve request")

    if req.status != "PENDING":
        raise ServiceError("Request already processed")

    if not get_member(planner, req.user_id):
        planner.members.append(
            Member(
                user_id=req.user_id,
                role=role,
                permissions=set(permissions),
            )
        )

    req.status = "APPROVED"
    planner.updated_at = now()

    log_action(
        state,
        planner.planner_id,
        actor_id,
        "REQUEST_APPROVED",
        f"id={request_id}",
    )

def reject_request(state, request_id: str, actor_id: str) -> None:
    req = next((r for r in state["requests"] if r.request_id == request_id), None)
    if not req:
        raise ServiceError("Request not found")

    planner = next((p for p in state["planners"] if p.planner_id == req.planner_id), None)
    if not planner:
        raise ServiceError("Planner not found")

    if not is_owner_or_admin(planner, actor_id):
        raise ServiceError("No permission to reject request")

    if req.status != "PENDING":
        raise ServiceError("Request already processed")

    req.status = "REJECTED"

    log_action(
        state,
        planner.planner_id,
        actor_id,
        "REQUEST_REJECTED",
        f"id={request_id}",
    )
