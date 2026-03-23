"""Inventory module."""

from .models import Car


class InventoryModule:
    """Tracks cars, parts, tools, and team cash."""

    def __init__(self, starting_cash: float = 0.0) -> None:
        self._cars: dict[int, Car] = {}
        self._parts: dict[str, int] = {}
        self._tools: dict[str, int] = {}
        self.cash_balance = float(starting_cash)
        self._next_car_id = 1

    def add_car(self, model: str, condition: int = 100) -> Car:
        model_name = model.strip()
        if not model_name:
            raise ValueError("Car model cannot be empty.")
        if condition < 0 or condition > 100:
            raise ValueError("Car condition must be between 0 and 100.")

        car = Car(car_id=self._next_car_id, model=model_name, condition=condition)
        if condition == 0:
            car.is_available = False
        self._cars[car.car_id] = car
        self._next_car_id += 1
        return car

    def get_car(self, car_id: int) -> Car:
        try:
            return self._cars[car_id]
        except KeyError as exc:
            raise ValueError(f"Car {car_id} does not exist in inventory.") from exc

    def list_cars(self) -> list[Car]:
        return list(self._cars.values())

    def list_available_cars(self, min_condition: int = 40) -> list[Car]:
        return [
            car
            for car in self._cars.values()
            if car.is_available and car.condition >= min_condition
        ]

    def set_car_availability(self, car_id: int, is_available: bool) -> Car:
        car = self.get_car(car_id)
        car.is_available = bool(is_available)
        return car

    def record_damage(self, car_id: int, damage_points: int) -> Car:
        if damage_points < 0:
            raise ValueError("Damage points cannot be negative.")
        car = self.get_car(car_id)
        car.condition = max(0, car.condition - damage_points)
        if car.condition < 40:
            car.is_available = False
        return car

    def repair_car(self, car_id: int, repair_points: int) -> Car:
        if repair_points <= 0:
            raise ValueError("Repair points must be greater than 0.")
        car = self.get_car(car_id)
        car.condition = min(100, car.condition + repair_points)
        if car.condition >= 40:
            car.is_available = True
        return car

    def add_spare_part(self, part_name: str, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("Part quantity must be greater than 0.")
        key = part_name.strip().lower()
        if not key:
            raise ValueError("Part name cannot be empty.")
        self._parts[key] = self._parts.get(key, 0) + quantity

    def add_tool(self, tool_name: str, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("Tool quantity must be greater than 0.")
        key = tool_name.strip().lower()
        if not key:
            raise ValueError("Tool name cannot be empty.")
        self._tools[key] = self._tools.get(key, 0) + quantity

    def get_parts(self) -> dict[str, int]:
        return dict(self._parts)

    def get_tools(self) -> dict[str, int]:
        return dict(self._tools)

    def adjust_cash(self, amount: float) -> float:
        new_balance = self.cash_balance + amount
        if new_balance < 0:
            raise ValueError("Insufficient cash balance for this transaction.")
        self.cash_balance = new_balance
        return self.cash_balance

