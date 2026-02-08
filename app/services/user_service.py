from typing import Optional
from app.models import User, GuestSession
from app.utils import new_id, now

class ServiceError(Exception):
    pass

def ensure_user(state, user_id: str) -> None:
    if not any(u.user_id == user_id for u in state["users"]):
        raise ServiceError("User not found")

def create_user(state, name: str, email: Optional[str]) -> User:
    if email:
        if any(u.email == email for u in state["users"]):
            raise ServiceError("User with this email already exists")

    user = User(
        user_id=new_id("user"),
        name=name,
        email=email,
    )
    state["users"].append(user)
    return user

def create_guest(state, username: str) -> GuestSession:
    guest = GuestSession(guest_id=new_id("guest"), user_name=username, created_at=now())
    state["guests"].append(guest)
    return guest
