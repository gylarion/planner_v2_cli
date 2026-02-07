from enum import Enum

class Role(str, Enum):
    OWNER = 'OWNER'
    ADMIN = 'ADMIN'
    MEMBER = 'MEMBER'
    GUEST_MEMBER = 'GUEST_MEMBER'

class AccessMode(str, Enum):
    FREE = 'FREE'
    REQUEST = 'REQUEST'

class Permission(str, Enum):
    EDIT_OWN_TASKS = 'can_edit_own_tasks'
    EDIT_ALL_TASKS = 'can_edit_all_tasks'
    MANAGE_MEMBERS = 'can_manage_members'
    MANAGE_SETTINGS = 'can_manage_settings'
    VIEW_LOGS = 'can_view_logs'