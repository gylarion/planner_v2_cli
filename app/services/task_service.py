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

def edit_task(
    state,
    task_id: str,
    actor_id: str,
    new_text: Optional[str] = None,
    new_deadline: Optional[str] = None,
) -> None:
    task = next((t for t in state["tasks"] if t.task_id == task_id), None)
    if not task:
        raise ServiceError("Task not found")

    planner = next((p for p in state["planners"] if p.planner_id == task.planner_id), None)
    if not planner:
        raise ServiceError("Planner not found")

    member = get_member(planner, actor_id)
    if not member:
        raise ServiceError("Not a member")

    if not can_edit_task(member, task):
        raise ServiceError("No permission to edit task")

    if new_text is not None:
        task.text = new_text

    if new_deadline is not None:
        from datetime import datetime
        task.deadline = datetime.fromisoformat(new_deadline)

    task.updated_at = now()
    planner.updated_at = now()

    log_action(
        state,
        planner.planner_id,
        actor_id,
        "TASK_UPDATED",
        f"task={task_id}",
    )

def delete_task(state, task_id: str, actor_id: str) -> None:
    task = next((t for t in state["tasks"] if t.task_id == task_id), None)
    if not task:
        raise ServiceError("Task not found")

    planner = next((p for p in state["planners"] if p.planner_id == task.planner_id), None)
    if not planner:
        raise ServiceError("Planner not found")

    member = get_member(planner, actor_id)
    if not member:
        raise ServiceError("Not a member")

    if not can_edit_task(member, task):
        raise ServiceError("No permission to delete task")

    state["tasks"].remove(task)
    planner.updated_at = now()

    log_action(
        state,
        planner.planner_id,
        actor_id,
        "TASK_DELETED",
        f"task={task_id}",
    )
