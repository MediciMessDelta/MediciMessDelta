"""
Transform: Cleaning & Enrichment (Phase 3, step 3) — built by Sloane.

Turns out Monah's ingestion module already does the enrichment work this
file was originally stubbed out to do: medici/ingestion/validation.py's
validate_row() already derives year/month/quarter/fiscal_year, infers
debit_account_type/credit_account_type (using the same keyword logic as
medici/accounting.py), and normalizes the branch name. By the time a row
comes out of the ingestion pipeline (load -> validate_all_rows ->
flag_duplicates), it's already a plain dict with every field the data
contract (medici/contracts.py) requires.

So clean.py's real job is smaller than planned: take those already-
enriched dicts and turn each one into an actual CleanedTransaction
object. Doing this matters for two reasons:
    1. Pydantic validation - CleanedTransaction(**row) checks every
       field is the right type (e.g. debit_amount really is a Decimal,
       date really is a date) and raises a clear error immediately if
       not, instead of a confusing bug three functions later.
    2. Everything downstream in Phase 3/4 (kpis.py, and Phase 4's
       anomaly rules) is written to expect CleanedTransaction objects
       with dot-access (row.branch), matching the fixtures in
       tests/fixtures.py - not raw dicts with row["branch"].
"""

from medici.contracts import CleanedTransaction


def to_cleaned_transaction(row):
    """Take one already-validated, already-deduped dict (as produced by
    medici.ingestion.validation.validate_row + medici.ingestion.dedup.
    flag_duplicates) and turn it into a CleanedTransaction object.

    Pydantic does the real work here: CleanedTransaction(**row) matches
    the dict's keys to the model's fields and validates each type.
    """
    return CleanedTransaction(**row)


def to_cleaned_transactions(rows):
    """Same as to_cleaned_transaction, but for a whole list of rows at
    once - this is the function kpis.py (and later, anomaly detection)
    will actually import and call on Monah's ingestion output."""
    return [to_cleaned_transaction(row) for row in rows]
