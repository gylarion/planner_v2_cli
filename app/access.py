from app.enums import Role, Permission
from app.models import Planner, Member, Task

def get_member(planner: Planner, user_id: str):
    for member in planner.members:
        if member.user_id == user_id:
            return member
    return None

def is_owner_or_admin(planner: Planner, user_id: str) -> bool:
    member = get_member(planner, user_id)
    return bool(member and member.role in {Role.OWNER, Role.ADMIN})

def can_manage_members(planner: Planner, user_id: str) -> bool:
    member = get_member(planner, user_id)
    return bool(member and (member.role == Role.OWNER or Permission.MANAGE_MEMBERS in member.permissions))

def can_view_logs(planner: Planner, user_id: str) -> bool:
    member = get_member(planner, user_id)
    return bool(member and (member.role in {Role.OWNER, Role.ADMIN} or Permission.VIEW_LOGS in member.permissions))

def can_edit_task(member: Member, task: Task) -> bool:
    if member.role in {Role.OWNER, Role.ADMIN}:
        return True

    if Permission.EDIT_ALL_TASKS in member.permissions:
        return True

    if (
        Permission.EDIT_OWN_TASKS in member.permissions
        and member.user_id == task.author_id
    ):
        return True
    return False