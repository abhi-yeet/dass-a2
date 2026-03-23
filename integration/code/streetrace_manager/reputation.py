"""Extra module: Crew reputation tracking."""

from .registration import RegistrationModule


class ReputationModule:
    """Tracks reputation points for crew members."""

    def __init__(self, registration: RegistrationModule):
        self.registration = registration
        self._reputation: dict[int, int] = {}

    def add_points(self, member_id: int, points: int) -> int:
        if points < 0:
            raise ValueError("Points to add must be non-negative.")
        self.registration.get_member(member_id)
        self._reputation[member_id] = self._reputation.get(member_id, 0) + points
        return self._reputation[member_id]

    def deduct_points(self, member_id: int, points: int) -> int:
        if points < 0:
            raise ValueError("Points to deduct must be non-negative.")
        self.registration.get_member(member_id)
        self._reputation[member_id] = max(0, self._reputation.get(member_id, 0) - points)
        return self._reputation[member_id]

    def get_points(self, member_id: int) -> int:
        self.registration.get_member(member_id)
        return self._reputation.get(member_id, 0)

    def leaderboard(self) -> list[tuple[int, int]]:
        return sorted(self._reputation.items(), key=lambda row: (-row[1], row[0]))

