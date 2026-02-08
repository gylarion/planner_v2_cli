from datetime import timedelta
from typing import Optional

from app.enums import Role, AccessMode, Permission
from app.models import Planner, Member
from app.utils import new_id, now
from app.services.log_service import log_action
from app.services.user_service import ensure_user, ServiceError


def create_planner(
    state,
    title: str,
    access_mode: AccessMode,
    owner_id: str,
    is_guest: bool,
    guest_id: Optional[str],
) -> Planner:

    if is_guest:
        if not any(g.guest_id == guest_id for g in state["guests"]):
            raise ServiceError("Guest not found")
    else:
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

def claim_guest_planner(
    state,
    planner_id: str,
    guest_id: str,
    user_id: str,
) -> None:
    planner = next((p for p in state["planners"] if p.planner_id == planner_id), None)
    if not planner:
        raise ServiceError("Planner not found")

    if not planner.is_guest:
        raise ServiceError("Planner is not a guest planner")

    if planner.expires_at and now() > planner.expires_at:
        raise ServiceError("Guest planner expired")

    if planner.guest_id != guest_id:
        raise ServiceError("Guest does not own this planner")

    planner.members = [
        m for m in planner.members
        if m.user_id != guest_id
    ]

    owner = Member(
        user_id=user_id,
        role=Role.OWNER,
        permissions={
            Permission.EDIT_ALL_TASKS,
            Permission.MANAGE_MEMBERS,
            Permission.MANAGE_SETTINGS,
            Permission.VIEW_LOGS,
        },
    )
    planner.members.append(owner)

    planner.is_guest = False
    planner.expires_at = None
    planner.guest_id = None
    planner.updated_at = now()

    log_action(
        state,
        planner.planner_id,
        user_id,
        "GUEST_PLANNER_CLAIMED",
        f"guest_id={guest_id}",
    )

def cleanup_guest_planners(state) -> int:
    current_time = now()

    expired_planners = [
        p for p in state["planners"]
        if p.is_guest and p.expires_at and p.expires_at < current_time
    ]

    removed_count = 0

    for planner in expired_planners:
        planner_id = planner.planner_id

        state["tasks"] = [
            t for t in state["tasks"]
            if t.planner_id != planner_id
        ]

        state["invites"] = [
            i for i in state["invites"]
            if i.planner_id != planner_id
        ]

        state["requests"] = [
            r for r in state["requests"]
            if r.planner_id != planner_id
        ]

        state["logs"] = [
            l for l in state["logs"]
            if l.planner_id != planner_id
        ]

        state["planners"].remove(planner)
        removed_count += 1

    return removed_count
