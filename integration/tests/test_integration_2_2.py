"""Integration tests for Assignment 2, Part 2.2."""

import pytest

from streetrace_manager.system import StreetRaceManager


def test_register_driver_then_enter_race_success() -> None:
    system = StreetRaceManager(starting_cash=1000)
    driver_id = system.register_and_assign("Rhea", "driver")
    car = system.inventory.add_car("Mazda RX-7", condition=95)

    race = system.race_management.create_race(
        name="Harbor Night Run",
        driver_id=driver_id,
        car_id=car.car_id,
        prize_pool=5000,
    )

    assert race.driver_id == driver_id
    assert race.car_id == car.car_id
    assert race.status == "SCHEDULED"


def test_enter_race_without_registered_driver_fails() -> None:
    system = StreetRaceManager(starting_cash=1000)
    car = system.inventory.add_car("Toyota Supra", condition=90)

    with pytest.raises(ValueError, match="not registered"):
        system.race_management.create_race(
            name="Tunnel Sprint",
            driver_id=999,
            car_id=car.car_id,
            prize_pool=3000,
        )


def test_non_driver_cannot_be_entered_in_race() -> None:
    system = StreetRaceManager(starting_cash=1000)
    mechanic_id = system.register_and_assign("Arjun", "mechanic")
    car = system.inventory.add_car("Honda NSX", condition=92)

    with pytest.raises(ValueError, match="cannot race"):
        system.race_management.create_race(
            name="Bypass Dash",
            driver_id=mechanic_id,
            car_id=car.car_id,
            prize_pool=2500,
        )


def test_race_results_update_rankings_and_inventory_cash() -> None:
    system = StreetRaceManager(starting_cash=2000)
    driver_id = system.register_and_assign("Ishaan", "driver")
    car = system.inventory.add_car("Nissan GT-R", condition=90)

    race = system.race_management.create_race(
        name="Coastal Clash",
        driver_id=driver_id,
        car_id=car.car_id,
        prize_pool=8000,
    )
    system.race_management.start_race(race.race_id)
    result = system.results.record_result(race_id=race.race_id, position=1)

    assert result.prize_money == 8000
    assert system.inventory.cash_balance == 10000
    assert system.results.get_rankings() == [(driver_id, 10)]


def test_damaged_car_mission_requires_mechanic_availability() -> None:
    system = StreetRaceManager(starting_cash=500)
    driver_id = system.register_and_assign("Mira", "driver")
    car = system.inventory.add_car("BMW M3", condition=88)

    race = system.race_management.create_race(
        name="Industrial Loop",
        driver_id=driver_id,
        car_id=car.car_id,
        prize_pool=3000,
    )
    system.race_management.start_race(race.race_id)
    system.results.record_result(
        race_id=race.race_id,
        position=2,
        car_damaged=True,
        damage_points=60,
    )

    assert system.inventory.get_car(car.car_id).is_available is False
    with pytest.raises(ValueError, match="required role 'mechanic' is unavailable"):
        system.mission_planning.create_mission(
            title="Urgent Repair",
            required_roles=["mechanic"],
        )


def test_assign_mission_validates_required_roles() -> None:
    system = StreetRaceManager(starting_cash=500)
    driver_id = system.register_and_assign("Kabir", "driver")
    mechanic_id = system.register_and_assign("Sara", "mechanic")

    mission = system.mission_planning.create_mission(
        title="Rescue Convoy",
        required_roles=["driver", "mechanic"],
        assigned_member_ids=[driver_id, mechanic_id],
    )

    started = system.mission_planning.start_mission(mission.mission_id)
    assert started.status == "IN_PROGRESS"

    completed = system.mission_planning.complete_mission(mission.mission_id)
    assert completed.status == "COMPLETED"


def test_mission_cannot_start_when_required_role_disappears() -> None:
    system = StreetRaceManager(starting_cash=500)
    member = system.registration.register_member("NoRole")
    system.crew_management.assign_role(member.member_id, "driver")
    mission = system.mission_planning.create_mission(
        title="Night Delivery",
        required_roles=["driver"],
        assigned_member_ids=[member.member_id],
    )

    system.crew_management.assign_role(member.member_id, "mechanic")
    with pytest.raises(ValueError, match="required role 'driver' is unavailable"):
        system.mission_planning.start_mission(mission.mission_id)
