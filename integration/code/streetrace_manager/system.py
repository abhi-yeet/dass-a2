"""Facade that integrates all StreetRace Manager modules."""

from .crew_management import CrewManagementModule
from .damage_control import DamageControlModule
from .inventory import InventoryModule
from .mission_planning import MissionPlanningModule
from .registration import RegistrationModule
from .reputation import ReputationModule
from .results import ResultsModule
from .race_management import RaceManagementModule


class StreetRaceManager:
    """High-level API for the integrated command-line system."""

    def __init__(self, starting_cash: float = 0.0) -> None:
        self.registration = RegistrationModule()
        self.crew_management = CrewManagementModule(self.registration)
        self.inventory = InventoryModule(starting_cash=starting_cash)
        self.race_management = RaceManagementModule(self.crew_management, self.inventory)
        self.results = ResultsModule(self.race_management, self.inventory)
        self.mission_planning = MissionPlanningModule(self.crew_management)
        self.damage_control = DamageControlModule(self.crew_management, self.inventory)
        self.reputation = ReputationModule(self.registration)

    def register_and_assign(self, name: str, role: str) -> int:
        member = self.registration.register_member(name)
        self.crew_management.assign_role(member.member_id, role)
        return member.member_id

    def run_race(
        self,
        race_name: str,
        driver_id: int,
        car_id: int,
        prize_pool: float,
        position: int,
        car_damaged: bool = False,
        damage_points: int = 0,
    ) -> dict:
        race = self.race_management.create_race(
            name=race_name,
            driver_id=driver_id,
            car_id=car_id,
            prize_pool=prize_pool,
        )
        self.race_management.start_race(race.race_id)
        result = self.results.record_result(
            race_id=race.race_id,
            position=position,
            car_damaged=car_damaged,
            damage_points=damage_points,
        )

        # Reward racers in extra Reputation module.
        rep_points = 15 if position == 1 else 8 if position == 2 else 5 if position == 3 else 2
        self.reputation.add_points(driver_id, rep_points)

        ticket_id = None
        if car_damaged and damage_points > 0:
            ticket_id = self.damage_control.open_damage_ticket(
                car_id=car_id,
                damage_points=damage_points,
                note=f"Damage from race {race.race_id}",
                apply_damage=False,
            )

        return {
            "race_id": race.race_id,
            "result": result,
            "cash_balance": self.inventory.cash_balance,
            "damage_ticket_id": ticket_id,
        }
