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