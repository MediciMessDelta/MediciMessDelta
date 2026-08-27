from datetime import datetime
from decimal import Decimal, InvalidOperation


def check_required_fields(row):
    """Looks at one row and checks that the important fields are
    actually filled in. Returns True if everything's there,
    False if something important is missing or blank."""

    required_fields = ["id", "date", "branch", "type", "counterparty",
                        "debit_account", "debit_amount",
                        "credit_account", "credit_amount"]

    for field in required_fields:
        value = row.get(field)
        if value is None or value.strip() == "":
            return False

    return True


def cleanup_date(date_text):
    """Takes date text like '1420-01-05' and turns it into a real
    date. Returns None if the text isn't a valid date."""

    try:
        result = datetime.strptime(date_text, "%Y-%m-%d").date()
        return result
    except ValueError:
        return None

def cleanup_amount(amount_text):
    """Takes amount text like '82833.66' and turns it into a
    precise Decimal number. Blank or missing text becomes 0.
    Returns None if the text isn't a valid number at all."""

    if amount_text is None or amount_text.strip() == "":
        return Decimal("0")

    try:
        return Decimal(amount_text.strip())
    except InvalidOperation:
        return None

def check_balance(row):
    """Checks that a row's debit and credit amounts actually balance.
    Returns True if they match, False if they don't (or if the
    amounts weren't valid numbers at all)."""

    debit = cleanup_amount(row.get("debit_amount"))
    credit = cleanup_amount(row.get("credit_amount"))
    credit_2 = cleanup_amount(row.get("credit_amount_2"))

    if debit is None or credit is None or credit_2 is None:
        return False

    if debit == credit + credit_2:
        return True
    else:
        return False   

def cleanup_branch(branch_text):
    """Removes extra blank space from the start/end of a branch name. Data exploration showed
    all branches were capitalized."""

    return branch_text.strip()

#using cleaned_date since it has already run through cleanup_date
def get_year(cleaned_date):
    """Pulls the year out of a real date."""
    return cleaned_date.year


def get_month(cleaned_date):
    """Pulls the month out of a real date, as a number 1-12."""
    return cleaned_date.month


def get_quarter(cleaned_date):
    """Figures out which quarter (Q1-Q4) a date falls in, based
    on its month."""

    month = cleaned_date.month

    if month <= 3:
        return "Q1"
    elif month <= 6:
        return "Q2"
    elif month <= 9:
        return "Q3"
    else:
        return "Q4"


def get_fiscal_year(cleaned_date):
    """The Medici Bank's fiscal year is Jan 1 to Dec 31, so this
    is just the same as the regular year."""
    return cleaned_date.year


def get_account_type(account_name):
    """Looks up whether an account is ASSET, LIABILITY, EQUITY, REVENUE,
    or EXPENSE. Uses the same keyword-matching logic as the real
    _infer_account_type in medici/accounting.py, so ingestion and the
    ledger never disagree on how an account is classified."""

    name_lower = account_name.strip().lower()

    asset_keywords = ["cash", "receivable", "inventory", "land", "building", "equipment", "asset"]
    liability_keywords = ["payable", "loan", "debt", "liability", "deposits payable"]
    equity_keywords = ["capital", "equity", "retained earnings", "owner"]
    revenue_keywords = ["revenue", "income", "sales", "interest income", "fee"]
    expense_keywords = ["expense", "wages", "rent", "supplies", "maintenance", "courier", "cost"]

    for keyword in asset_keywords:
        if keyword in name_lower:
            return "ASSET"

    for keyword in liability_keywords:
        if keyword in name_lower:
            return "LIABILITY"

    for keyword in equity_keywords:
        if keyword in name_lower:
            return "EQUITY"

    for keyword in revenue_keywords:
        if keyword in name_lower:
            return "REVENUE"

    for keyword in expense_keywords:
        if keyword in name_lower:
            return "EXPENSE"

    return "ASSET"  # if all cases dont match return asset

def validate_row(row):
    """Takes one record (row) and tries to build a clean version of it.
    Gives back two things: the cleaned row, and a rejection reason.
    If the row is good, cleaned row will be filled in and reason
    will be None. If the row is bad, cleaned row will be None and
    reason will explain why, so nothing gets dropped or ignored."""

    if not check_required_fields(row):
        return None, "missing required fields"

    real_date = cleanup_date(row["date"])
    if real_date is None:
        return None, "invalid date: " + str(row.get("date"))

    if not check_balance(row):
        return None, "debit and credit amounts do not balance"

    debit_amount = cleanup_amount(row.get("debit_amount"))
    credit_amount = cleanup_amount(row.get("credit_amount"))
    credit_amount_2 = cleanup_amount(row.get("credit_amount_2"))

    raw_credit_account_2 = row.get("credit_account_2")
    if raw_credit_account_2 is None or raw_credit_account_2.strip() == "":
        credit_account_2 = None
    else:
        credit_account_2 = raw_credit_account_2.strip()

    cleaned_row = {
        "id": int(row["id"]),
        "date": real_date,
        "branch": cleanup_branch(row["branch"]),
        "type": row["type"].strip(),
        "counterparty": row.get("counterparty", "").strip(),
        "description": row.get("description", "").strip(),
        "debit_account": row["debit_account"].strip(),
        "debit_amount": debit_amount,
        "credit_account": row["credit_account"].strip(),
        "credit_amount": credit_amount,
        "credit_account_2": credit_account_2,
        "credit_amount_2": credit_amount_2,
        "currency": row.get("currency", "florin").strip(),
        "year": get_year(real_date),
        "month": get_month(real_date),
        "quarter": get_quarter(real_date),
        "fiscal_year": get_fiscal_year(real_date),
        "debit_account_type": get_account_type(row["debit_account"]),
        "credit_account_type": get_account_type(row["credit_account"]),
        "is_duplicate": False,
    }

    return cleaned_row, None

def validate_all_rows(raw_rows):
    """Runs validate_row function on a whole list of records (rows). Gives back two
    lists; the cleaned rows, and the rejected ones (with reasons),
    so nothing is missed or unaccounted for i.e transactions."""

    cleaned_rows = []
    rejected_rows = []

    for row in raw_rows:
        cleaned_row, reason = validate_row(row)
        if cleaned_row is not None:
            cleaned_rows.append(cleaned_row)
        else:
            rejected_rows.append({"id": row.get("id"), "reason": reason})

    return cleaned_rows, rejected_rows