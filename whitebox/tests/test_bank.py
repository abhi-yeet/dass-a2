"""White-box tests for the Bank module.

These tests cover collect, pay_out, give_loan, and summary helpers,
including edge cases for zero/negative amounts and insufficient funds.

Error found:
  - Error 7: give_loan() credits the player but does NOT reduce the
    bank's own funds, violating the docstring ('The bank's own funds
    are reduced accordingly').
"""

import pytest
from moneypoly.player import Player
from moneypoly.bank import Bank
from moneypoly.config import BANK_STARTING_FUNDS


# ── Branch: collect() positive amount ────────────────────────────

def test_collect_positive():
    """Collecting a positive amount should increase bank funds.

    Why needed: Taxes, fines, and purchase prices flow into the bank
    via collect(). The funds and total_collected must both update.
    """
    bank = Bank()
    bank.collect(500)
    assert bank.get_balance() == BANK_STARTING_FUNDS + 500


# ── Branch: pay_out() normal ─────────────────────────────────────

def test_pay_out_normal():
    """Paying out a valid amount should reduce bank funds and return it.

    Why needed: Card rewards and salary are paid via pay_out(). The
    returned value must match the requested amount.
    """
    bank = Bank()
    paid = bank.pay_out(200)
    assert paid == 200
    assert bank.get_balance() == BANK_STARTING_FUNDS - 200


# ── Branch: pay_out() zero or negative → returns 0 ──────────────

def test_pay_out_zero():
    """Paying out $0 should return 0 and not change funds.

    Why needed: Some card values are 0 (e.g. jail cards). pay_out
    must handle this gracefully.
    """
    bank = Bank()
    assert bank.pay_out(0) == 0
    assert bank.get_balance() == BANK_STARTING_FUNDS


def test_pay_out_negative():
    """Paying out a negative amount should return 0.

    Why needed: Guards against adding money to the bank via pay_out.
    """
    bank = Bank()
    assert bank.pay_out(-100) == 0


# ── Branch: pay_out() insufficient funds → ValueError ────────────

def test_pay_out_insufficient_funds():
    """Paying out more than the bank has should raise ValueError.

    Why needed: The bank is not infinite — it must refuse payouts
    it cannot cover.
    """
    bank = Bank()
    with pytest.raises(ValueError):
        bank.pay_out(BANK_STARTING_FUNDS + 1)


# ── Branch: give_loan() positive amount ──────────────────────────

def test_give_loan_credits_player():
    """give_loan() should increase the player's balance.

    Why needed: Emergency loans let struggling players stay in the
    game. The player must actually receive the money.
    """
    bank = Bank()
    player = Player("Alice")
    bank.give_loan(player, 500)
    assert player.balance == 1500 + 500


def test_give_loan_deducts_from_bank():
    """give_loan() should reduce the bank's funds by the loan amount.

    Why needed: The docstring states 'The bank's own funds are reduced
    accordingly', but the implementation never subtracts from _funds.
    This means the bank creates money from thin air.

    Error found (Error 7): Missing `self._funds -= amount` in give_loan().
    """
    bank = Bank()
    player = Player("Alice")
    bank.give_loan(player, 500)
    assert bank.get_balance() == BANK_STARTING_FUNDS - 500, (
        "Bank funds should decrease after issuing a loan"
    )


def test_give_loan_records_loan():
    """give_loan() should record the loan in the loans list.

    Why needed: total_loans_issued() and loan_count() rely on this
    list for reporting.
    """
    bank = Bank()
    player = Player("Alice")
    bank.give_loan(player, 300)
    assert bank.loan_count() == 1
    assert bank.total_loans_issued() == 300


# ── Branch: give_loan() zero or negative → no-op ────────────────

def test_give_loan_zero():
    """Requesting a $0 loan should be a no-op.

    Why needed: Edge case — a zero loan shouldn't change balances
    or appear in the loan list.
    """
    bank = Bank()
    player = Player("Alice")
    bank.give_loan(player, 0)
    assert player.balance == 1500
    assert bank.loan_count() == 0


def test_give_loan_negative():
    """Requesting a negative loan should be a no-op.

    Why needed: Prevents using give_loan to steal money from a player.
    """
    bank = Bank()
    player = Player("Alice")
    bank.give_loan(player, -100)
    assert player.balance == 1500
    assert bank.loan_count() == 0


# ── Helpers ──────────────────────────────────────────────────────

def test_total_loans_issued_sums_correctly():
    """total_loans_issued() should sum all loan amounts.

    Why needed: Validates the aggregate reporting function.
    """
    bank = Bank()
    p1 = Player("Alice")
    p2 = Player("Bob")
    bank.give_loan(p1, 100)
    bank.give_loan(p2, 250)
    assert bank.total_loans_issued() == 350
    assert bank.loan_count() == 2


def test_summary_does_not_crash():
    """summary() should print without errors.

    Why needed: Smoke test for the formatted output function.
    """
    bank = Bank()
    bank.collect(1000)
    bank.summary()  # Should not raise
