from medici.ingestion.dedup import flag_duplicates
from medici.ingestion.loaders import load_csv, load_json, load_since
from medici.ingestion.validation import validate_all_rows


def test_csv_and_json_load_same_row_count():
    csv_rows = load_csv('medici_transactions.csv')
    json_rows = load_json('medici_transactions.json')
    assert len(csv_rows) == len(json_rows)


def test_all_real_rows_pass_validation():
    rows = load_csv('medici_transactions.csv')
    cleaned_rows, rejected_rows = validate_all_rows(rows)
    assert len(cleaned_rows) == 80230
    assert len(rejected_rows) == 0


def test_invalid_row_gets_rejected_not_dropped():
    bad_row = {
        'id': '999999', 'date': '1420-01-01', 'branch': 'Florence',
        'type': 'deposit', 'counterparty': 'Test', 'debit_account': 'Cash',
        'debit_amount': '100.00', 'credit_account': 'Deposits',
        'credit_amount': '40.00', 'credit_amount_2': '',
    }
    cleaned_rows, rejected_rows = validate_all_rows([bad_row])
    assert len(cleaned_rows) == 0
    assert len(rejected_rows) == 1
    assert rejected_rows[0]['id'] == '999999'


def test_no_duplicates_in_real_data():
    rows = load_csv('medici_transactions.csv')
    cleaned_rows, rejected_rows = validate_all_rows(rows)
    cleaned_rows = flag_duplicates(cleaned_rows)

    duplicate_count = 0
    for row in cleaned_rows:
        if row['is_duplicate']:
            duplicate_count += 1

    assert duplicate_count == 0


def test_load_since_returns_only_newer_rows():
    rows = load_csv('medici_transactions.csv')
    new_rows = load_since(rows, 80000)
    assert len(new_rows) == 230
    assert new_rows[0]['id'] == '80001'