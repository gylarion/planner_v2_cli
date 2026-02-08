from app.models import LogEntry
from app.utils import new_id, now


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
