from typing import Optional

from app.access import can_edit_task, get_member
from app.models import Task
from app.utils import new_id, now
from app.services.log_service import log_action
from app.services.user_service import ServiceError


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
