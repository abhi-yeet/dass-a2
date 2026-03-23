"""Results module."""

from .inventory import InventoryModule
from .models import RaceResult
from .race_management import RaceManagementModule


class ResultsModule:
    """Records race outcomes, updates rankings, and handles prize money."""

    def __init__(self, race_management: RaceManagementModule, inventory: InventoryModule):
        self.race_management = race_management
        self.inventory = inventory
        self._results: dict[int, RaceResult] = {}
        self._driver_points: dict[int, int] = {}

    def record_result(
        self,
        race_id: int,
        position: int,
        car_damaged: bool = False,
        damage_points: int = 0,
    ) -> RaceResult:
        if position < 1:
            raise ValueError("Race position must be >= 1.")
        if damage_points < 0:
            raise ValueError("Damage points cannot be negative.")

        race = self.race_management.get_race(race_id)
        if race.status == "COMPLETED" and race_id in self._results:
            raise ValueError(f"Result for race {race_id} has already been recorded.")

        prize_money = self._calculate_prize(race.prize_pool, position)
        result = RaceResult(
            race_id=race_id,
            driver_id=race.driver_id,
            position=position,
            prize_money=prize_money,
            car_damaged=car_damaged,
            damage_points=damage_points if car_damaged else 0,
        )

        self._results[race_id] = result
        self.inventory.adjust_cash(prize_money)

        if car_damaged and damage_points > 0:
            self.inventory.record_damage(race.car_id, damage_points)

        self._driver_points[race.driver_id] = (
            self._driver_points.get(race.driver_id, 0) + self._points_for_position(position)
        )
        self.race_management.finish_race(race_id)
        return result

    def get_result(self, race_id: int) -> RaceResult:
        try:
            return self._results[race_id]
        except KeyError as exc:
            raise ValueError(f"No result exists for race {race_id}.") from exc

    def get_rankings(self) -> list[tuple[int, int]]:
        return sorted(
            self._driver_points.items(),
            key=lambda row: (-row[1], row[0]),
        )

    @staticmethod
    def _calculate_prize(prize_pool: float, position: int) -> float:
        if position == 1:
            return prize_pool
        if position == 2:
            return prize_pool * 0.5
        if position == 3:
            return prize_pool * 0.25
        return 0.0

    @staticmethod
    def _points_for_position(position: int) -> int:
        if position == 1:
            return 10
        if position == 2:
            return 6
        if position == 3:
            return 4
        return 1

