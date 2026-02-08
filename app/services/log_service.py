from app.enums import Role, Permission
from app.models import LogEntry
from app.services.user_service import ServiceError
from app.utils import new_id, now
from typing import List
from app.access import get_member


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

def list_logs(state, planner_id: str, actor_id: str) -> List[LogEntry]:
    planner = next((p for p in state["planners"] if p.planner_id == planner_id), None)
    if not planner:
        raise ServiceError("Planner not found")

    member = get_member(planner, actor_id)
    if not member:
        raise ServiceError("Not a member")

    if (
        member.role not in {Role.OWNER, Role.ADMIN}
        and Permission.VIEW_LOGS not in member.permissions
    ):
        raise ServiceError("No permission to view logs")

    return [
        log for log in state["logs"]
        if log.planner_id == planner_id
    ]
