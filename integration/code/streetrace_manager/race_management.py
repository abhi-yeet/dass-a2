"""Race Management module."""

from .crew_management import CrewManagementModule
from .inventory import InventoryModule
from .models import Race


class RaceManagementModule:
    """Creates and manages races using registered drivers and available cars."""

    def __init__(self, crew_management: CrewManagementModule, inventory: InventoryModule):
        self.crew_management = crew_management
        self.inventory = inventory
        self._races: dict[int, Race] = {}
        self._next_race_id = 1

    def create_race(
        self,
        name: str,
        driver_id: int,
        car_id: int,
        prize_pool: float,
    ) -> Race:
        if prize_pool < 0:
            raise ValueError("Prize pool cannot be negative.")

        driver = self.crew_management.registration.get_member(driver_id)
        if driver.role != "driver":
            raise ValueError(
                f"Member {driver_id} cannot race because role is '{driver.role}'."
            )

        car = self.inventory.get_car(car_id)
        if not car.is_available:
            raise ValueError(f"Car {car_id} is not available.")

        race = Race(
            race_id=self._next_race_id,
            name=name.strip() or f"Race-{self._next_race_id}",
            driver_id=driver_id,
            car_id=car_id,
            prize_pool=float(prize_pool),
        )
        self._races[race.race_id] = race
        self._next_race_id += 1
        return race

    def get_race(self, race_id: int) -> Race:
        try:
            return self._races[race_id]
        except KeyError as exc:
            raise ValueError(f"Race {race_id} does not exist.") from exc

    def list_races(self) -> list[Race]:
        return list(self._races.values())

    def start_race(self, race_id: int) -> Race:
        race = self.get_race(race_id)
        if race.status != "SCHEDULED":
            raise ValueError(
                f"Race {race_id} cannot start from status '{race.status}'."
            )
        car = self.inventory.get_car(race.car_id)
        if not car.is_available:
            raise ValueError(f"Car {race.car_id} became unavailable before race start.")
        race.status = "IN_PROGRESS"
        self.inventory.set_car_availability(race.car_id, False)
        return race

    def finish_race(self, race_id: int) -> Race:
        race = self.get_race(race_id)
        if race.status not in {"SCHEDULED", "IN_PROGRESS"}:
            raise ValueError(
                f"Race {race_id} cannot be finished from status '{race.status}'."
            )
        race.status = "COMPLETED"
        car = self.inventory.get_car(race.car_id)
        self.inventory.set_car_availability(race.car_id, car.condition >= 40)
        return race
