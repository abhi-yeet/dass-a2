"""Registration module."""

from .models import CrewMember


class RegistrationModule:
    """Registers and stores all crew members."""

    def __init__(self) -> None:
        self._members: dict[int, CrewMember] = {}
        self._next_member_id = 1

    def register_member(self, name: str, role: str | None = None) -> CrewMember:
        cleaned_name = name.strip()
        if not cleaned_name:
            raise ValueError("Crew member name cannot be empty.")

        member = CrewMember(
            member_id=self._next_member_id,
            name=cleaned_name,
            role=role.strip().lower() if role else None,
        )
        self._members[member.member_id] = member
        self._next_member_id += 1
        return member

    def get_member(self, member_id: int) -> CrewMember:
        try:
            return self._members[member_id]
        except KeyError as exc:
            raise ValueError(f"Crew member {member_id} is not registered.") from exc

    def list_members(self) -> list[CrewMember]:
        return list(self._members.values())

