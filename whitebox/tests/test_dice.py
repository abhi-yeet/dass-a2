"""White-box tests for the Dice module.

These tests cover every branch of the Dice class, including roll outcomes,
doubles detection, streak tracking, reset behaviour, and the describe helper.

Error found:
  - Error 1: dice.py uses randint(1, 5) instead of randint(1, 6),
    meaning dice can never roll a 6. A six-sided die must produce
    values in [1, 6].
"""

from unittest.mock import patch
from moneypoly.dice import Dice


# ── Branch: roll() produces a valid total ────────────────────────

def test_roll_returns_sum_of_two_dice():
    """Each roll should return the sum of both dice faces.

    Why needed: Ensures the basic contract of roll() — that it returns
    die1 + die2 — holds for any random outcome.
    """
    dice = Dice()
    with patch("moneypoly.dice.random.randint", side_effect=[3, 4]):
        total = dice.roll()
    assert total == 7
    assert dice.die1 == 3
    assert dice.die2 == 4


# ── Branch: is_doubles() True vs False ──────────────────────────

def test_is_doubles_true_when_same():
    """Rolling the same value on both dice should count as doubles.

    Why needed: Doubles give the player an extra turn and, after three
    in a row, send them to jail. We must verify the flag is set.
    """
    dice = Dice()
    with patch("moneypoly.dice.random.randint", side_effect=[3, 3]):
        dice.roll()
    assert dice.is_doubles() is True


def test_is_doubles_false_when_different():
    """Different values on the two dice should NOT be doubles.

    Why needed: Ensures non-doubles are correctly distinguished, so
    a player doesn't accidentally get extra turns.
    """
    dice = Dice()
    with patch("moneypoly.dice.random.randint", side_effect=[2, 5]):
        dice.roll()
    assert dice.is_doubles() is False


# ── Branch: doubles_streak increments / resets ──────────────────

def test_doubles_streak_increments():
    """Rolling consecutive doubles should increase the streak counter.

    Why needed: Three consecutive doubles send the player to jail.
    This test verifies the counter increments correctly.
    """
    dice = Dice()
    with patch("moneypoly.dice.random.randint", side_effect=[2, 2]):
        dice.roll()
    assert dice.doubles_streak == 1
    with patch("moneypoly.dice.random.randint", side_effect=[4, 4]):
        dice.roll()
    assert dice.doubles_streak == 2


def test_doubles_streak_resets_on_non_doubles():
    """A non-doubles roll should reset the streak to zero.

    Why needed: Once a player breaks the doubles chain, the counter
    must restart. Otherwise they'd be unfairly sent to jail.
    """
    dice = Dice()
    with patch("moneypoly.dice.random.randint", side_effect=[3, 3]):
        dice.roll()
    assert dice.doubles_streak == 1
    with patch("moneypoly.dice.random.randint", side_effect=[1, 4]):
        dice.roll()
    assert dice.doubles_streak == 0


# ── Branch: reset() ──────────────────────────────────────────────

def test_reset_clears_state():
    """reset() should zero out die faces and the doubles streak.

    Why needed: Ensures dice state doesn't leak between games.
    """
    dice = Dice()
    with patch("moneypoly.dice.random.randint", side_effect=[5, 5]):
        dice.roll()
    dice.reset()
    assert dice.die1 == 0
    assert dice.die2 == 0
    assert dice.doubles_streak == 0


# ── Branch: describe() with and without doubles ─────────────────

def test_describe_non_doubles():
    """describe() should format a non-doubles roll without a tag.

    Why needed: Verify the human-readable output is correct for the
    most common case (no doubles).
    """
    dice = Dice()
    with patch("moneypoly.dice.random.randint", side_effect=[2, 5]):
        dice.roll()
    assert dice.describe() == "2 + 5 = 7"


def test_describe_doubles():
    """describe() should append '(DOUBLES)' when both dice match.

    Why needed: Players need a visual cue that doubles were rolled.
    """
    dice = Dice()
    with patch("moneypoly.dice.random.randint", side_effect=[4, 4]):
        dice.roll()
    assert "(DOUBLES)" in dice.describe()


# ── ERROR 1: dice range is 1–5 instead of 1–6 ───────────────────

def test_dice_range_includes_six():
    """A six-sided die must be able to produce the value 6.

    Why needed: The docstring says 'six-sided dice', but randint(1, 5)
    limits the range to [1, 5]. This means a roll of 6 on either die
    is impossible, skewing probabilities and reducing the maximum
    combined roll from 12 to 10.

    Error found: randint(1, 5) should be randint(1, 6).
    """
    dice = Dice()
    with patch("moneypoly.dice.random.randint", side_effect=[6, 6]):
        total = dice.roll()
    assert total == 12, (
        "A six-sided die must support value 6; "
        "randint(1, 5) makes this impossible"
    )
