"""White-box tests for the Player module.

These tests cover all branches in Player, including money operations,
movement with Go salary logic, jail mechanics, property management,
and status helpers.

Error found:
  - Error 4: move() only awards the Go salary when the player lands
    exactly on position 0, but NOT when they pass through Go
    (e.g. moving from position 38 by 4 to position 2).
"""

import pytest
from moneypoly.player import Player
from moneypoly.config import STARTING_BALANCE, GO_SALARY, BOARD_SIZE


# ── Branch: add_money positive / negative ────────────────────────

def test_add_money_increases_balance():
    """Adding a positive amount should increase the player's balance.

    Why needed: Core financial operation — must work correctly for
    rent, salary, and card rewards.
    """
    player = Player("Alice")
    player.add_money(200)
    assert player.balance == STARTING_BALANCE + 200


def test_add_money_negative_raises():
    """Adding a negative amount should raise ValueError.

    Why needed: Prevents accidental balance corruption by enforcing
    the non-negative precondition.
    """
    player = Player("Alice")
    with pytest.raises(ValueError):
        player.add_money(-50)


# ── Branch: deduct_money positive / negative ─────────────────────

def test_deduct_money_decreases_balance():
    """Deducting a positive amount should reduce the player's balance.

    Why needed: Used for rent, taxes, and purchases — must subtract
    correctly.
    """
    player = Player("Alice")
    player.deduct_money(300)
    assert player.balance == STARTING_BALANCE - 300


def test_deduct_money_negative_raises():
    """Deducting a negative amount should raise ValueError.

    Why needed: Guards against accidentally increasing balance through
    a deduction call.
    """
    player = Player("Alice")
    with pytest.raises(ValueError):
        player.deduct_money(-100)


# ── Branch: is_bankrupt ──────────────────────────────────────────

def test_is_bankrupt_when_zero():
    """A player with exactly $0 should be considered bankrupt.

    Why needed: Edge case — the boundary between solvent and bankrupt.
    """
    player = Player("Alice", balance=0)
    assert player.is_bankrupt() is True


def test_is_bankrupt_when_negative():
    """A player with negative balance should be bankrupt.

    Why needed: After paying rent or taxes, balance can go negative.
    """
    player = Player("Alice", balance=-10)
    assert player.is_bankrupt() is True


def test_not_bankrupt_when_positive():
    """A player with positive balance is NOT bankrupt.

    Why needed: Normal case — most of the game the player is solvent.
    """
    player = Player("Alice", balance=100)
    assert player.is_bankrupt() is False


# ── Branch: move() wrapping and Go salary ────────────────────────

def test_move_normal():
    """Moving forward without wrapping should update position correctly.

    Why needed: The most common case — ensures basic movement works.
    """
    player = Player("Alice")
    player.position = 5
    new_pos = player.move(3)
    assert new_pos == 8
    assert player.balance == STARTING_BALANCE  # No Go salary


def test_move_landing_on_go():
    """Landing exactly on Go (position 0) should award the salary.

    Why needed: Covers the branch where position == 0 after move.
    """
    player = Player("Alice")
    player.position = BOARD_SIZE - 5
    new_pos = player.move(5)
    assert new_pos == 0
    assert player.balance == STARTING_BALANCE + GO_SALARY


def test_move_passing_go_awards_salary():
    """Passing through Go (wrapping past position 0) should award salary.

    Why needed: The docstring says 'Awards the Go salary if the player
    passes or lands on Go', but the code only checks position == 0.
    A player moving from position 38 by 4 (to position 2) passes Go
    but never lands on it, so they miss the $200.

    Error found (Error 4): The move() method fails to detect passing
    Go when the new position is nonzero. It should compare old and
    new positions to detect a wrap-around.
    """
    player = Player("Alice")
    player.position = 38
    new_pos = player.move(4)  # wraps: (38+4) % 40 = 2
    assert new_pos == 2
    assert player.balance == STARTING_BALANCE + GO_SALARY, (
        "Player passed Go but did not receive $200 salary"
    )


# ── Branch: go_to_jail ───────────────────────────────────────────

def test_go_to_jail():
    """go_to_jail() should move the player to jail and set jail flags.

    Why needed: Jail is a key game mechanic. Position, in_jail flag,
    and jail_turns must all be set correctly.
    """
    player = Player("Alice")
    player.position = 30
    player.go_to_jail()
    assert player.position == 10
    assert player.in_jail is True
    assert player.jail_turns == 0


# ── Branch: add_property duplicate guard ─────────────────────────

def test_add_property_no_duplicates():
    """Adding the same property twice should not create a duplicate.

    Why needed: Without this guard, a player's property list could
    bloat, leading to incorrect net worth and rent calculations.
    """
    player = Player("Alice")

    class FakeProp:
        """Minimal stand-in for a Property object."""
        name = "Park Place"
    prop = FakeProp()
    player.add_property(prop)
    player.add_property(prop)
    assert len(player.properties) == 1


# ── Branch: remove_property present / absent ─────────────────────

def test_remove_property():
    """Removing an owned property should shrink the list by one.

    Why needed: Used during trades and bankruptcy — must not crash
    or leave stale entries.
    """
    player = Player("Alice")

    class FakeProp:
        """Minimal stand-in for a Property object."""
        name = "Boardwalk"
    prop = FakeProp()
    player.add_property(prop)
    player.remove_property(prop)
    assert len(player.properties) == 0


def test_remove_property_not_owned():
    """Removing a property the player doesn't own should be a no-op.

    Why needed: Prevents crashes if game logic tries to remove a
    property that was already traded away.
    """
    player = Player("Alice")

    class FakeProp:
        """Minimal stand-in for a Property object."""
        name = "Boardwalk"
    prop = FakeProp()
    player.remove_property(prop)  # Should not raise
    assert len(player.properties) == 0


# ── Branch: status_line jail tag ─────────────────────────────────

def test_status_line_not_jailed():
    """status_line() should NOT include [JAILED] for a free player.

    Why needed: The UI must accurately reflect player state.
    """
    player = Player("Alice")
    assert "[JAILED]" not in player.status_line()


def test_status_line_jailed():
    """status_line() should include [JAILED] for a jailed player.

    Why needed: Ensures jailed status is visible in standings.
    """
    player = Player("Alice")
    player.in_jail = True
    assert "[JAILED]" in player.status_line()


# ── net_worth ────────────────────────────────────────────────────

def test_net_worth_equals_balance():
    """net_worth() should return the player's current balance.

    Why needed: net_worth is used by find_winner() to determine
    the game's winner.
    """
    player = Player("Alice", balance=750)
    assert player.net_worth() == 750
