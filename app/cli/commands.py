from app.enums import AccessMode, Role
from app.services.user_service import create_user, create_guest, ServiceError
from app.services.planner_service import (
    create_planner,
    cleanup_guest_planners,
)
from app.services.task_service import add_task, edit_task, delete_task
from app.services.access_service import create_invite, accept_invite
from app.services.log_service import list_logs


def handle_command(state, ctx, raw: str) -> None:
    parts = raw.split()
    cmd = parts[0]

# -------- CONTEXT CHECKS --------

    if cmd in (
        "create-planner", "add-task", "edit-task",
        "delete-task", "invite", "logs"
    ) and not ctx.current_user_id:
        print("Please login first (login-user / login-guest)")
        return

    if cmd in (
        "add-task", "edit-task", "delete-task",
        "invite", "logs"
    ) and not ctx.current_planner_id:
        print("Please select planner first (use-planner <planner_id>)")
        return

# -------- HELP --------

    if cmd == "help":
        print_help()
        return

# -------- USER / GUEST --------

    if cmd == "create-user":
        if len(parts) < 2:
            print("Usage: create-user <name> [email]")
            return

        name = parts[1]
        email = parts[2] if len(parts) > 2 else None
        user = create_user(state, name, email)
        print(f"User created: {user.user_id}")
        return

    if cmd == "create-guest":
        if len(parts) < 2:
            print("Usage: create-guest <name>")
            return

        guest = create_guest(state, parts[1])
        print(f"Guest created: {guest.guest_id}")
        return

    if cmd == "login-user":
        if len(parts) != 2:
            print("Usage: login-user <user_id>")
            return

        user_id = parts[1]
        if not any(u.user_id == user_id for u in state["users"]):
            print("User not found. Use create-user first.")
            return

        ctx.current_user_id = user_id
        ctx.current_planner_id = None
        print(f"Logged in as user {user_id}")
        return

    if cmd == "login-guest":
        if len(parts) != 2:
            print("Usage: login-guest <guest_id>")
            return

        guest_id = parts[1]
        if not any(g.guest_id == guest_id for g in state["guests"]):
            print("Guest not found. Use create-guest first.")
            return

        ctx.current_user_id = guest_id
        ctx.current_planner_id = None
        print(f"Logged in as guest {guest_id}")
        return

    # -------- PLANNER --------

    if cmd == "create-planner":
        if len(parts) < 3:
            print("Usage: create-planner <title> <FREE|REQUEST>")
            return

        title = parts[1]

        try:
            access_mode = AccessMode(parts[2].upper())
        except KeyError:
            print("Invalid access mode. Use FREE or REQUEST")
            return

        planner = create_planner(
            state,
            title=title,
            access_mode=access_mode,
            owner_id=ctx.current_user_id,
            is_guest=ctx.current_user_id.startswith("guest_"),
            guest_id=ctx.current_user_id if ctx.current_user_id.startswith("guest_") else None,
        )

        ctx.current_planner_id = planner.planner_id
        print(f"Planner created and selected: {planner.planner_id}")
        return

    if cmd == "use-planner":
        if len(parts) != 2:
            print("Usage: use-planner <planner_id>")
            return

        planner_id = parts[1]
        if not any(p.planner_id == planner_id for p in state["planners"]):
            print("Planner not found")
            return

        ctx.current_planner_id = planner_id
        print(f"Using planner {planner_id}")
        return

    if cmd == "cleanup":
        removed = cleanup_guest_planners(state)
        print(f"Removed {removed} expired guest planners")
        return

# -------- TASKS --------

    if cmd == "add-task":
        if len(parts) < 2:
            print("Usage: add-task <text>")
            return

        text = " ".join(parts[1:])
        task = add_task(
            state,
            planner_id=ctx.current_planner_id,
            actor_id=ctx.current_user_id,
            text=text,
            deadline=None,
        )
        print(f"Task created: {task.task_id}")
        return

    if cmd == "edit-task":
        if len(parts) < 3:
            print("Usage: edit-task <task_id> <new text>")
            return

        edit_task(
            state,
            task_id=parts[1],
            actor_id=ctx.current_user_id,
            new_text=" ".join(parts[2:]),
        )
        print("Task updated")
        return

    if cmd == "delete-task":
        if len(parts) < 2:
            print("Usage: delete-task <task_id>")
            return

        delete_task(state, parts[1], ctx.current_user_id)
        print("Task deleted")
        return

# -------- ACCESS --------

    if cmd == "invite":
        if len(parts) < 2:
            print("Usage: invite <MEMBER|ADMIN>")
            return

        try:
            role = Role(parts[1].upper())
        except KeyError:
            print("Invalid role. Use MEMBER or ADMIN")
            return

        invite = create_invite(
            state,
            planner_id=ctx.current_planner_id,
            issuer_id=ctx.current_user_id,
            role=role,
        )
        print(f"Invite created: {invite.invite_code}")
        return

    if cmd == "accept-invite":
        if len(parts) < 2:
            print("Usage: accept-invite <invite_code>")
            return

        accept_invite(state, parts[1], ctx.current_user_id)
        print("Invite accepted")
        return

# -------- LOGS --------

    if cmd == "logs":
        logs = list_logs(state, ctx.current_planner_id, ctx.current_user_id)
        for l in logs:
            print(f"[{l.created_at}] {l.action} {l.details}")
        return


    print("Unknown command. Type 'help'.")


def print_help() -> None:
    print(
        """
+----------------+---------------------------------------------+---------------------------------------------+
| CATEGORY       | COMMAND                                     | DESCRIPTION                                 |
+----------------+---------------------------------------------+---------------------------------------------+
| AUTH           | create-user <name> [email]                  | Create registered user                      |
|                | create-guest <name>                         | Create guest session                        |
|                | login-user <user_id>                        | Login as user                               |
|                | login-guest <guest_id>                      | Login as guest                              |
+----------------+---------------------------------------------+---------------------------------------------+
| PLANNER        | create-planner <title> <FREE|REQUEST>       | Create and select planner                   |
|                | use-planner <planner_id>                    | Select existing planner                    |
|                | cleanup                                     | Remove expired guest planners               |
+----------------+---------------------------------------------+---------------------------------------------+
| TASKS          | add-task <text>                             | Add task to current planner                 |
|                | edit-task <task_id> <new text>              | Edit existing task                          |
|                | delete-task <task_id>                       | Delete task                                 |
+----------------+---------------------------------------------+---------------------------------------------+
| ACCESS         | invite <MEMBER|ADMIN>                       | Create invite link                          |
|                | accept-invite <invite_code>                 | Accept invite                               |
+----------------+---------------------------------------------+---------------------------------------------+
| LOGS           | logs                                        | Show planner logs                           |
+----------------+---------------------------------------------+---------------------------------------------+
| SYSTEM         | help                                        | Show this help                              |
|                | exit                                        | Exit CLI                                    |
+----------------+---------------------------------------------+---------------------------------------------+
"""
    )
