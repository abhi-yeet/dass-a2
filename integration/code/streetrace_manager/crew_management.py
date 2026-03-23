"""Crew Management module."""

from .models import CrewMember
from .registration import RegistrationModule


class CrewManagementModule:
    """Manages role assignments and skill levels for registered members."""

    ALLOWED_ROLES = {"driver", "mechanic", "strategist", "scout", "technician"}

    def __init__(self, registration: RegistrationModule) -> None:
        self.registration = registration

    def assign_role(self, member_id: int, role: str) -> CrewMember:
        role_key = role.strip().lower()
        if role_key not in self.ALLOWED_ROLES:
            raise ValueError(
                f"Invalid role '{role}'. Allowed roles: {sorted(self.ALLOWED_ROLES)}"
            )

        member = self.registration.get_member(member_id)
        member.role = role_key
        return member

    def set_skill_level(self, member_id: int, skill: str, level: int) -> CrewMember:
        if level < 1 or level > 10:
            raise ValueError("Skill level must be between 1 and 10.")
        skill_name = skill.strip().lower()
        if not skill_name:
            raise ValueError("Skill name cannot be empty.")

        member = self.registration.get_member(member_id)
        member.skill_levels[skill_name] = level
        return member

    def members_with_role(self, role: str) -> list[CrewMember]:
        role_key = role.strip().lower()
        return [m for m in self.registration.list_members() if m.role == role_key]

    def has_available_role(self, role: str) -> bool:
        return bool(self.members_with_role(role))

