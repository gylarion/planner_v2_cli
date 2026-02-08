from typing import Optional

from app.access import can_manage_members, is_owner_or_admin, get_member
from app.enums import Role, Permission, AccessMode
from app.models import Invite, AccessRequest, Member
from app.utils import new_id, now
from app.services.log_service import log_action
from app.services.user_service import ensure_user, ServiceError

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

def update_member_role(
    state,
    planner_id: str,
    actor_id: str,
    target_user_id: str,
    new_role: Role,
) -> None:
    planner = next((p for p in state["planners"] if p.planner_id == planner_id), None)
    if not planner:
        raise ServiceError("Planner not found")

    if not is_owner_or_admin(planner, actor_id):
        raise ServiceError("No permission to update member roles")

    if actor_id == target_user_id:
        raise ServiceError("Cannot change own role")

    target = get_member(planner, target_user_id)
    if not target:
        raise ServiceError("Target user is not a member")

    if target.role == Role.OWNER:
        raise ServiceError("Cannot change OWNER role")

    if new_role == Role.OWNER:
        raise ServiceError("Cannot assign OWNER role")

    if new_role == Role.ADMIN:
        permissions = {
            Permission.EDIT_ALL_TASKS,
            Permission.MANAGE_MEMBERS,
            Permission.VIEW_LOGS,
        }
    elif new_role == Role.MEMBER:
        permissions = {Permission.EDIT_OWN_TASKS}
    else:
        permissions = set()

    target.role = new_role
    target.permissions = permissions

    planner.updated_at = now()
    log_action(
        state,
        planner_id,
        actor_id,
        "MEMBER_ROLE_UPDATED",
        f"user={target_user_id}, role={new_role.value}",
    )

