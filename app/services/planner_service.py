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
