"""
This is the ingestion part of the project, built by Me (Monah) in Phase 2.

It reads the raw transaction data from the CSV and JSON files, checks each
row to make sure it's valid, cleans it up, and flags any duplicates it finds.

The cleaned rows this produces get used next by Sloane's code in Phase 3
and 4, which calculates KPIs and looks for suspicious activity.
"""