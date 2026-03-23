# 2.2 Integration Test Design (StreetRace Manager)

## Test Case 1: Register a driver and enter the driver into a race
- Scenario: Register a crew member as `driver`, add a car, then create a race.
- Modules involved: Registration, Crew Management, Inventory, Race Management
- Expected result: Race is created with `SCHEDULED` status, linked to the registered driver and car.
- Actual result: Passed.
- Why needed: Validates the basic happy-path integration and confirms registration/role data flows into race creation.

## Test Case 2: Enter race without a registered driver
- Scenario: Try to create a race using a non-existent member ID.
- Modules involved: Race Management, Registration
- Expected result: Race creation fails with a registration error.
- Actual result: Passed (`ValueError` raised).
- Why needed: Ensures rule enforcement that a member must exist before race participation.

## Test Case 3: Enter race with registered but non-driver member
- Scenario: Register a member as `mechanic` and attempt race entry.
- Modules involved: Registration, Crew Management, Race Management
- Expected result: Race creation fails because only `driver` role is allowed.
- Actual result: Passed (`ValueError` raised).
- Why needed: Verifies role-based validation during module interaction.

## Test Case 4: Complete race and verify results + prize money update inventory
- Scenario: Create and start race, record first-place result.
- Modules involved: Race Management, Results, Inventory
- Expected result: Result is stored, rankings updated, and prize amount added to cash balance.
- Actual result: Passed (cash increased correctly; rankings updated).
- Why needed: Directly checks core data flow from race outcome to finance and ranking state.

## Test Case 5: Damaged car flow and mission role validation
- Scenario: Record race damage that makes car unavailable, then create mechanic-required mission with no mechanic in crew.
- Modules involved: Results, Inventory, Mission Planning, Crew Management
- Expected result: Damaged car becomes unavailable; mission creation fails due to missing mechanic role.
- Actual result: Passed (`ValueError` raised for missing mechanic role).
- Why needed: Validates a specific business-rule chain required in the assignment.

## Test Case 6: Assign mission with required roles and complete mission lifecycle
- Scenario: Register driver + mechanic, create mission requiring both, start and complete mission.
- Modules involved: Registration, Crew Management, Mission Planning
- Expected result: Mission transitions `PLANNED -> IN_PROGRESS -> COMPLETED`.
- Actual result: Passed.
- Why needed: Ensures role validation and mission lifecycle work correctly across modules.

## Test Case 7: Mission cannot start when required role becomes unavailable
- Scenario: Create mission requiring `driver`, then reassign only driver to another role before mission start.
- Modules involved: Crew Management, Mission Planning
- Expected result: Mission start fails because required role is no longer available.
- Actual result: Passed (`ValueError` raised).
- Why needed: Confirms mission start re-validates current state instead of trusting stale configuration.

## Test execution summary
- Test file: `integration/tests/test_integration_2_2.py`
- Command: `pytest -q integration/tests/test_integration_2_2.py`
- Result: `7 passed`

