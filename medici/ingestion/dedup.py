def get_duplicate_key(row):
    """Builds a tuple used to check if two rows look like duplicates,
    based on the six fields the team agreed on."""
    return (row["date"], row["branch"], row["type"], row["counterparty"],
             row["debit_amount"], row["credit_account"])


def flag_duplicates(cleaned_rows):
    """Marks is_duplicate = True on every row that shares its key
    with another row. Rows are never removed, just flagged."""

    key_counts = {}
    for row in cleaned_rows:
        key = get_duplicate_key(row)
        if key in key_counts:
            key_counts[key] = key_counts[key] + 1
        else:
            key_counts[key] = 1

    for row in cleaned_rows:
        key = get_duplicate_key(row)
        if key_counts[key] > 1:
            row["is_duplicate"] = True
        else:
            row["is_duplicate"] = False

    return cleaned_rows