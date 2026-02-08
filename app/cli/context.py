class CLIContext:
    def __init__(self):
        self.current_user_id = None
        self.current_planner_id = None

    def format_prompt(self, state) -> str:
        parts = []

        if self.current_user_id:
            user = next(
                (u for u in state["users"] if u.user_id == self.current_user_id),
                None,
            )
            guest = next(
                (g for g in state["guests"] if g.guest_id == self.current_user_id),
                None,
            )

            if user:
                parts.append(f"UserName : {user.name} | user_id -({user.user_id})")
            elif guest:
                parts.append(f"GuestName={guest.user_name}| guest_id - ({guest.guest_id})")

        if self.current_planner_id:
            planner = next(
                (p for p in state["planners"] if p.planner_id == self.current_planner_id),
                None,
            )
            if planner:
                parts.append(f"name_planner: {planner.title}| planner_id - ({planner.planner_id})")

        if parts:
            return "[" + " | ".join(parts) + "] > "

        return "> "
