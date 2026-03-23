# DASS Assignment 2

Git Repository: https://github.com/abhi-yeet/dass-a2.git

## How to Run the Code

### Whitebox (MoneyPoly)
From the project root:

```bash
python3 whitebox/code/main.py
```

## How to Run the Tests

### Whitebox Tests
From the project root:

```bash
pytest -q whitebox/tests
```

### Integration Tests
From the project root:

```bash
pytest -q integration/tests
```

### Blackbox API Tests (QuickCart)
1. Start the QuickCart API server (default expected URL: `http://localhost:8080`).
2. Set required environment variables (example):

```bash
export QC_BASE_URL="http://localhost:8080"
export QC_ROLL_NUMBER="20260001"
```

3. Run tests from the project root:

```bash
pytest -q blackbox/tests
```

## Notes

- If `pytest` is not installed, install dependencies first (for example, `pip install pytest requests`).
- Blackbox tests are skipped automatically when the API server is unreachable.
