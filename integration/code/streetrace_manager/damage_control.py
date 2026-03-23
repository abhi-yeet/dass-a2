"""Extra module: Damage Control and repair operations."""

from .crew_management import CrewManagementModule
from .inventory import InventoryModule


class DamageControlModule:
    """
    Handles damaged cars and validates mechanic availability before repairs.
    """

    def __init__(self, crew_management: CrewManagementModule, inventory: InventoryModule):
        self.crew_management = crew_management
        self.inventory = inventory
        self._tickets: dict[int, dict] = {}
        self._next_ticket_id = 1

    def open_damage_ticket(
        self,
        car_id: int,
        damage_points: int,
        note: str = "",
        apply_damage: bool = True,
    ) -> int:
        if damage_points <= 0:
            raise ValueError("Damage points must be greater than 0.")

        car = (
            self.inventory.record_damage(car_id, damage_points)
            if apply_damage
            else self.inventory.get_car(car_id)
        )
        ticket_id = self._next_ticket_id
        self._tickets[ticket_id] = {
            "ticket_id": ticket_id,
            "car_id": car.car_id,
            "damage_points": damage_points,
            "note": note.strip(),
            "status": "OPEN",
            "assigned_mechanic_id": None,
        }
        self._next_ticket_id += 1
        return ticket_id

    def assign_mechanic(self, ticket_id: int, mechanic_id: int) -> dict:
        ticket = self.get_ticket(ticket_id)
        member = self.crew_management.registration.get_member(mechanic_id)
        if member.role != "mechanic":
            raise ValueError(f"Member {mechanic_id} is not a mechanic.")
        ticket["assigned_mechanic_id"] = mechanic_id
        return ticket

    def repair_from_ticket(self, ticket_id: int, repair_points: int) -> dict:
        ticket = self.get_ticket(ticket_id)
        if ticket["status"] != "OPEN":
            raise ValueError(f"Ticket {ticket_id} is already closed.")
        if ticket["assigned_mechanic_id"] is None:
            raise ValueError("Cannot repair without an assigned mechanic.")
        if not self.crew_management.has_available_role("mechanic"):
            raise ValueError("Repair mission cannot proceed because no mechanic is available.")

        self.inventory.repair_car(ticket["car_id"], repair_points)
        ticket["status"] = "CLOSED"
        return ticket

    def get_ticket(self, ticket_id: int) -> dict:
        try:
            return self._tickets[ticket_id]
        except KeyError as exc:
            raise ValueError(f"Damage ticket {ticket_id} does not exist.") from exc

    def list_tickets(self) -> list[dict]:
        return list(self._tickets.values())
