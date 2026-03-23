"""Mission Planning module."""

from .crew_management import CrewManagementModule
from .models import Mission


class MissionPlanningModule:
    """Assigns missions and validates required role availability."""

    def __init__(self, crew_management: CrewManagementModule):
        self.crew_management = crew_management
        self._missions: dict[int, Mission] = {}
        self._next_mission_id = 1

    def create_mission(
        self,
        title: str,
        required_roles: list[str],
        assigned_member_ids: list[int] | None = None,
        linked_car_id: int | None = None,
    ) -> Mission:
        normalized_roles = [role.strip().lower() for role in required_roles if role.strip()]
        if not normalized_roles:
            raise ValueError("Mission must require at least one role.")

        self._ensure_roles_available(normalized_roles)

        assigned_ids = assigned_member_ids or []
        if assigned_ids:
            self._validate_assignees_cover_roles(assigned_ids, normalized_roles)

        mission = Mission(
            mission_id=self._next_mission_id,
            title=title.strip() or f"Mission-{self._next_mission_id}",
            required_roles=normalized_roles,
            assigned_member_ids=list(assigned_ids),
            linked_car_id=linked_car_id,
        )
        self._missions[mission.mission_id] = mission
        self._next_mission_id += 1
        return mission

    def start_mission(self, mission_id: int) -> Mission:
        mission = self.get_mission(mission_id)
        if mission.status != "PLANNED":
            raise ValueError(
                f"Mission {mission_id} cannot start from status '{mission.status}'."
            )
        self._ensure_roles_available(mission.required_roles)
        mission.status = "IN_PROGRESS"
        return mission

    def complete_mission(self, mission_id: int) -> Mission:
        mission = self.get_mission(mission_id)
        if mission.status != "IN_PROGRESS":
            raise ValueError(
                f"Mission {mission_id} cannot complete from status '{mission.status}'."
            )
        mission.status = "COMPLETED"
        return mission

    def get_mission(self, mission_id: int) -> Mission:
        try:
            return self._missions[mission_id]
        except KeyError as exc:
            raise ValueError(f"Mission {mission_id} does not exist.") from exc

    def list_missions(self) -> list[Mission]:
        return list(self._missions.values())

    def _ensure_roles_available(self, roles: list[str]) -> None:
        for role in roles:
            if not self.crew_management.has_available_role(role):
                raise ValueError(
                    f"Mission cannot proceed because required role '{role}' is unavailable."
                )

    def _validate_assignees_cover_roles(
        self,
        assigned_member_ids: list[int],
        required_roles: list[str],
    ) -> None:
        assignee_roles = []
        for member_id in assigned_member_ids:
            member = self.crew_management.registration.get_member(member_id)
            if member.role is None:
                raise ValueError(f"Member {member_id} has no assigned role.")
            assignee_roles.append(member.role)

        missing_roles = [role for role in required_roles if role not in assignee_roles]
        if missing_roles:
            raise ValueError(
                f"Assigned crew does not cover required roles: {sorted(set(missing_roles))}"
            )

