"""White-box tests for the Game module.

These tests cover buy_property, pay_rent, mortgage/unmortgage,
trade, find_winner, and card-related logic.

Errors found:
  - Error 2: find_winner() uses min() instead of max(), returning
    the POOREST player as the winner.
  - Error 5: buy_property() uses '<=' to compare balance to price,
    so a player with exactly enough money cannot buy.
  - Error 6: pay_rent() deducts rent from the tenant but never
    credits it to the property owner.
"""

from unittest.mock import patch
from moneypoly.game import Game
from moneypoly.player import Player
from moneypoly.property import Property, PropertyGroup
from moneypoly.bank import Bank
from moneypoly.cards import CardDeck


# ── helpers ──────────────────────────────────────────────────────

def _simple_game():
    """Create a Game with two players for testing."""
    game = Game(["Alice", "Bob"])
    return game


def _game_with_property(owner_index=0):
    """Create a game where one player owns a property."""
    game = _simple_game()
    prop = game.board.properties[0]  # Mediterranean Avenue
    owner = game.players[owner_index]
    prop.owner = owner
    owner.add_property(prop)
    return game, prop


# ── ERROR 5: buy_property balance == price ───────────────────────

def test_buy_property_exact_balance():
    """A player with exactly enough money should be able to buy.

    Why needed: If a property costs $60 and the player has exactly
    $60, they should be allowed to purchase it. The current code uses
    '<=' which incorrectly blocks this purchase.

    Error found (Error 5): The condition `player.balance <= prop.price`
    should be `player.balance < prop.price`.
    """
    game = _simple_game()
    player = game.players[0]
    prop = game.board.properties[0]  # price = 60
    player.balance = 60
    result = game.buy_property(player, prop)
    assert result is True, (
        "Player with exact balance should be able to buy; "
        "buy_property uses <= instead of <"
    )
    assert prop.owner == player


def test_buy_property_insufficient():
    """A player without enough money should be rejected.

    Why needed: Covers the branch where the player cannot afford
    the property.
    """
    game = _simple_game()
    player = game.players[0]
    prop = game.board.properties[0]  # price = 60
    player.balance = 50
    result = game.buy_property(player, prop)
    assert result is False


def test_buy_property_success():
    """A player with more than enough should buy successfully.

    Why needed: Happy path — verifies balance deduction, ownership
    transfer, and bank collection all happen.
    """
    game = _simple_game()
    player = game.players[0]
    prop = game.board.properties[0]  # price = 60
    initial_balance = player.balance
    result = game.buy_property(player, prop)
    assert result is True
    assert player.balance == initial_balance - prop.price
    assert prop.owner == player
    assert prop in player.properties


# ── ERROR 6: pay_rent doesn't credit owner ───────────────────────

def test_pay_rent_credits_owner():
    """Rent paid by the tenant should be credited to the property owner.

    Why needed: Rent is the primary income mechanism for property
    owners. If the owner never receives the rent, the game's economy
    is broken — tenants lose money that simply vanishes.

    Error found (Error 6): pay_rent() calls player.deduct_money(rent)
    but never calls prop.owner.add_money(rent).
    """
    game, prop = _game_with_property(owner_index=0)
    owner = game.players[0]
    tenant = game.players[1]
    owner_initial = owner.balance
    tenant_initial = tenant.balance
    rent = prop.get_rent()

    game.pay_rent(tenant, prop)

    assert tenant.balance == tenant_initial - rent
    assert owner.balance == owner_initial + rent, (
        "Owner should receive the rent payment; "
        "pay_rent never calls owner.add_money()"
    )


def test_pay_rent_mortgaged_no_charge():
    """No rent should be collected on a mortgaged property.

    Why needed: Covers the branch where is_mortgaged is True.
    """
    game, prop = _game_with_property()
    prop.is_mortgaged = True
    tenant = game.players[1]
    initial = tenant.balance
    game.pay_rent(tenant, prop)
    assert tenant.balance == initial  # No deduction


def test_pay_rent_no_owner():
    """No rent should be collected on an unowned property.

    Why needed: Covers the branch where owner is None.
    """
    game = _simple_game()
    prop = game.board.properties[0]
    prop.owner = None
    tenant = game.players[0]
    initial = tenant.balance
    game.pay_rent(tenant, prop)
    assert tenant.balance == initial


# ── ERROR 2: find_winner uses min instead of max ─────────────────

def test_find_winner_returns_richest():
    """find_winner() should return the player with the highest net worth.

    Why needed: The winner of Monopoly is the richest player when the
    game ends. Using min() instead of max() returns the poorest.

    Error found (Error 2): find_winner() uses min(..., key=net_worth)
    which returns the player with the LOWEST net worth.
    """
    game = _simple_game()
    game.players[0].balance = 3000  # Alice is richer
    game.players[1].balance = 500   # Bob is poorer
    winner = game.find_winner()
    assert winner.name == "Alice", (
        "find_winner should return the richest player; "
        "it uses min() instead of max()"
    )


def test_find_winner_no_players():
    """find_winner() should return None when no players remain.

    Why needed: Edge case — if all players are bankrupted.
    """
    game = _simple_game()
    game.players.clear()
    assert game.find_winner() is None


# ── mortgage_property ────────────────────────────────────────────

def test_mortgage_property_success():
    """Mortgaging an owned property should credit half-price and return True.

    Why needed: Verifies the happy path of the mortgage flow.
    """
    game, prop = _game_with_property()
    owner = game.players[0]
    initial = owner.balance
    result = game.mortgage_property(owner, prop)
    assert result is True
    assert owner.balance == initial + prop.mortgage_value


def test_mortgage_property_not_owned():
    """Mortgaging a property you don't own should fail.

    Why needed: Covers the owner != player branch.
    """
    game, prop = _game_with_property(owner_index=0)
    other = game.players[1]
    result = game.mortgage_property(other, prop)
    assert result is False


def test_mortgage_property_already_mortgaged():
    """Mortgaging an already-mortgaged property should fail.

    Why needed: Covers the payout == 0 branch (double mortgage).
    """
    game, prop = _game_with_property()
    owner = game.players[0]
    game.mortgage_property(owner, prop)
    result = game.mortgage_property(owner, prop)
    assert result is False


# ── unmortgage_property ──────────────────────────────────────────

def test_unmortgage_property_success():
    """Unmortgaging should deduct the 110% cost and return True.

    Why needed: Verifies the happy path of unmortgage.
    """
    game, prop = _game_with_property()
    owner = game.players[0]
    game.mortgage_property(owner, prop)
    balance_after_mortgage = owner.balance
    result = game.unmortgage_property(owner, prop)
    assert result is True
    expected_cost = int(prop.mortgage_value * 1.1)
    assert owner.balance == balance_after_mortgage - expected_cost


def test_unmortgage_not_mortgaged():
    """Unmortgaging a non-mortgaged property should fail.

    Why needed: Covers the cost == 0 branch.
    """
    game, prop = _game_with_property()
    owner = game.players[0]
    result = game.unmortgage_property(owner, prop)
    assert result is False


def test_unmortgage_not_owned():
    """Unmortgaging a property you don't own should fail.

    Why needed: Covers the owner != player branch.
    """
    game, prop = _game_with_property(owner_index=0)
    other = game.players[1]
    result = game.unmortgage_property(other, prop)
    assert result is False


def test_unmortgage_insufficient_funds():
    """Unmortgaging when too poor should fail.

    Why needed: Covers the balance < cost branch.
    """
    game, prop = _game_with_property()
    owner = game.players[0]
    game.mortgage_property(owner, prop)
    owner.balance = 0
    result = game.unmortgage_property(owner, prop)
    assert result is False


# ── trade ────────────────────────────────────────────────────────

def test_trade_success():
    """A valid trade should transfer property and cash.

    Why needed: Covers the happy path — ownership and balances must
    update correctly.
    """
    game, prop = _game_with_property(owner_index=0)
    seller = game.players[0]
    buyer = game.players[1]
    seller_initial = seller.balance
    buyer_initial = buyer.balance
    result = game.trade(seller, buyer, prop, 100)
    assert result is True
    assert prop.owner == buyer
    assert buyer.balance == buyer_initial - 100
    assert prop in buyer.properties
    assert prop not in seller.properties


def test_trade_seller_doesnt_own():
    """Trade should fail if the seller doesn't own the property.

    Why needed: Covers the ownership check branch.
    """
    game, prop = _game_with_property(owner_index=0)
    result = game.trade(game.players[1], game.players[0], prop, 50)
    assert result is False


def test_trade_buyer_cannot_afford():
    """Trade should fail if the buyer can't afford the cash amount.

    Why needed: Covers the balance < cash_amount branch.
    """
    game, prop = _game_with_property(owner_index=0)
    buyer = game.players[1]
    buyer.balance = 10
    result = game.trade(game.players[0], buyer, prop, 100)
    assert result is False


# ── advance_turn ─────────────────────────────────────────────────

def test_advance_turn_wraps():
    """advance_turn should cycle through players.

    Why needed: Ensures proper round-robin turn ordering.
    """
    game = _simple_game()
    assert game.current_index == 0
    game.advance_turn()
    assert game.current_index == 1
    game.advance_turn()
    assert game.current_index == 0  # Wraps back


# ── _check_bankruptcy ────────────────────────────────────────────

def test_check_bankruptcy_removes_player():
    """A bankrupt player should be eliminated and their properties freed.

    Why needed: Covers the is_bankrupt() → True branch and all the
    cleanup logic inside _check_bankruptcy.
    """
    game, prop = _game_with_property(owner_index=0)
    owner = game.players[0]
    owner.balance = 0  # Bankrupt
    game._check_bankruptcy(owner)
    assert owner.is_eliminated is True
    assert prop.owner is None
    assert owner not in game.players


def test_check_bankruptcy_solvent_no_change():
    """A solvent player should not be affected.

    Why needed: Covers the is_bankrupt() → False branch.
    """
    game = _simple_game()
    player = game.players[0]
    game._check_bankruptcy(player)
    assert player.is_eliminated is False
    assert player in game.players


# ── CardDeck basics ──────────────────────────────────────────────

def test_card_deck_draw_cycles():
    """Drawing more cards than the deck size should cycle back.

    Why needed: The deck is finite; it must wrap around rather than
    crashing with an index error.
    """
    cards = [{"description": "A", "action": "collect", "value": 10},
             {"description": "B", "action": "pay", "value": 5}]
    deck = CardDeck(cards)
    first = deck.draw()
    second = deck.draw()
    third = deck.draw()  # Should cycle back to first
    assert third["description"] == "A"


def test_card_deck_empty():
    """Drawing from an empty deck should return None.

    Why needed: Edge case — prevents crashes when no cards exist.
    """
    deck = CardDeck([])
    assert deck.draw() is None
    assert deck.peek() is None
