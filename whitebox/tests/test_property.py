"""White-box tests for the Property and PropertyGroup modules.

These tests cover rent calculation (mortgaged, normal, full-group),
mortgage/unmortgage operations, availability checks, group ownership,
and owner counts.

Error found:
  - Error 3: PropertyGroup.all_owned_by() uses any() instead of all(),
    so it returns True even when only ONE property in the group is
    owned by the player, causing rent to be doubled prematurely.
"""

from moneypoly.property import Property, PropertyGroup


# ── helpers ──────────────────────────────────────────────────────

def _make_group_with_props(n=2):
    """Create a PropertyGroup with `n` properties for testing."""
    group = PropertyGroup("TestGroup", "blue")
    props = []
    for i in range(n):
        prop = Property(f"Prop{i}", position=i, price=100,
                        base_rent=10, group=group)
        props.append(prop)
    return group, props


class FakeOwner:
    """Minimal stand-in for a Player."""
    def __init__(self, name="Owner"):
        self.name = name


# ── Branch: get_rent() mortgaged → 0 ────────────────────────────

def test_get_rent_mortgaged_returns_zero():
    """A mortgaged property should yield zero rent.

    Why needed: Mortgaging is how players raise cash; while mortgaged,
    no rent should be charged to other players.
    """
    group, (prop,) = _make_group_with_props(1)
    prop.is_mortgaged = True
    assert prop.get_rent() == 0


# ── Branch: get_rent() full group → doubled ──────────────────────

def test_get_rent_full_group_doubles_rent():
    """Owning all properties in a group should double the rent.

    Why needed: This is a core Monopoly rule — completing a colour
    set rewards the player with higher income.

    Error found (Error 3): all_owned_by() incorrectly uses any()
    instead of all(). If only one of the two properties is owned
    by the player, this test will still pass because any() returns
    True. The explicit two-property test below catches this bug.
    """
    owner = FakeOwner()
    group, props = _make_group_with_props(2)
    for prop in props:
        prop.owner = owner
    # With all owned, rent should be base * 2
    assert props[0].get_rent() == 10 * 2


def test_get_rent_partial_group_no_bonus():
    """Owning only SOME properties in a group should NOT double rent.

    Why needed: If a player owns 1 of 2 properties in a group, rent
    should remain at base rate. This test directly exposes Error 3:
    all_owned_by() uses any() and incorrectly returns True.
    """
    owner = FakeOwner()
    other_owner = FakeOwner("Other")
    group, props = _make_group_with_props(2)
    props[0].owner = owner
    props[1].owner = other_owner  # Different owner
    # Only one property owned → should be base rent, NOT doubled
    assert props[0].get_rent() == 10, (
        "Rent should not be doubled when player owns only part of "
        "the group; all_owned_by() likely uses any() instead of all()"
    )


# ── Branch: get_rent() no group ──────────────────────────────────

def test_get_rent_no_group():
    """A property with no group should return base rent.

    Why needed: Some properties (like railroads) might not belong
    to a colour group.
    """
    prop = Property("Solo", position=5, price=200, base_rent=25)
    assert prop.get_rent() == 25


# ── Branch: mortgage() already mortgaged → 0 ─────────────────────

def test_mortgage_returns_value():
    """Mortgaging an unmortgaged property should return half the price.

    Why needed: The payout is how a player raises emergency cash.
    """
    prop = Property("Test", position=1, price=200, base_rent=10)
    payout = prop.mortgage()
    assert payout == 100
    assert prop.is_mortgaged is True


def test_mortgage_already_mortgaged():
    """Mortgaging an already mortgaged property should return 0.

    Why needed: Prevents double-mortgaging, which would give free money.
    """
    prop = Property("Test", position=1, price=200, base_rent=10)
    prop.mortgage()
    assert prop.mortgage() == 0


# ── Branch: unmortgage() not mortgaged → 0, else → cost ──────────

def test_unmortgage_returns_cost():
    """Unmortgaging should return the 110% redemption cost.

    Why needed: The cost to redeem is higher than the mortgage payout,
    representing interest. This must be calculated correctly.
    """
    prop = Property("Test", position=1, price=200, base_rent=10)
    prop.mortgage()
    cost = prop.unmortgage()
    assert cost == int(100 * 1.1)  # 110
    assert prop.is_mortgaged is False


def test_unmortgage_not_mortgaged():
    """Unmortgaging a non-mortgaged property should return 0.

    Why needed: Guards against paying redemption cost on a free property.
    """
    prop = Property("Test", position=1, price=200, base_rent=10)
    assert prop.unmortgage() == 0


# ── Branch: is_available ─────────────────────────────────────────

def test_is_available_unowned():
    """An unowned, unmortgaged property should be available for purchase.

    Why needed: This flag gates whether the Buy option is shown.
    """
    prop = Property("Test", position=1, price=100, base_rent=5)
    assert prop.is_available() is True


def test_is_available_owned():
    """An owned property should NOT be available.

    Why needed: Prevents a property from being bought twice.
    """
    prop = Property("Test", position=1, price=100, base_rent=5)
    prop.owner = FakeOwner()
    assert prop.is_available() is False


def test_is_available_mortgaged():
    """A mortgaged property should NOT be available.

    Why needed: Mortgaged properties cannot be re-purchased.
    """
    prop = Property("Test", position=1, price=100, base_rent=5)
    prop.mortgage()
    assert prop.is_available() is False


# ── PropertyGroup: all_owned_by ──────────────────────────────────

def test_all_owned_by_none_returns_false():
    """all_owned_by(None) should return False.

    Why needed: Before any properties are purchased, owner is None.
    The function must not crash or return True.
    """
    group, _ = _make_group_with_props(2)
    assert group.all_owned_by(None) is False


# ── PropertyGroup: get_owner_counts ──────────────────────────────

def test_get_owner_counts():
    """get_owner_counts() should map each owner to their property count.

    Why needed: Used to determine whether a player has a monopoly.
    """
    owner = FakeOwner()
    group, props = _make_group_with_props(3)
    props[0].owner = owner
    props[1].owner = owner
    counts = group.get_owner_counts()
    assert counts[owner] == 2


def test_get_owner_counts_empty():
    """When no properties are owned, the counts dict should be empty.

    Why needed: Edge case at the start of a game.
    """
    group, _ = _make_group_with_props(2)
    assert group.get_owner_counts() == {}


# ── PropertyGroup: size ──────────────────────────────────────────

def test_group_size():
    """size() should return the number of properties in the group.

    Why needed: Validates that property registration works correctly.
    """
    group, _ = _make_group_with_props(3)
    assert group.size() == 3


# ── PropertyGroup: add_property ──────────────────────────────────

def test_add_property_to_group():
    """add_property() should register the property and back-link it.

    Why needed: Ensures the bidirectional link between Property and
    PropertyGroup is established correctly.
    """
    group = PropertyGroup("Green", "green")
    prop = Property("Pacific Ave", position=31, price=300, base_rent=26)
    group.add_property(prop)
    assert prop in group.properties
    assert prop.group is group


def test_add_property_no_duplicate():
    """Adding the same property twice should not create duplicates.

    Why needed: Prevents inflated group sizes.
    """
    group = PropertyGroup("Green", "green")
    prop = Property("Pacific Ave", position=31, price=300, base_rent=26)
    group.add_property(prop)
    group.add_property(prop)
    assert len(group.properties) == 1
