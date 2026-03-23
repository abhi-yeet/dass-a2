"""Shared domain models for StreetRace Manager."""

from dataclasses import dataclass, field


@dataclass
class CrewMember:
    member_id: int
    name: str
    role: str | None = None
    skill_levels: dict[str, int] = field(default_factory=dict)


@dataclass
class Car:
    car_id: int
    model: str
    condition: int = 100
    is_available: bool = True


@dataclass
class Race:
    race_id: int
    name: str
    driver_id: int
    car_id: int
    prize_pool: float
    status: str = "SCHEDULED"


@dataclass
class RaceResult:
    race_id: int
    driver_id: int
    position: int
    prize_money: float
    car_damaged: bool = False
    damage_points: int = 0


@dataclass
class Mission:
    mission_id: int
    title: str
    required_roles: list[str]
    assigned_member_ids: list[int]
    linked_car_id: int | None = None
    status: str = "PLANNED"

