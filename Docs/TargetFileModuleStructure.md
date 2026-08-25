# MediciMessDelta — Recommended End-State File & Module Structure

Prepared as an expert recommendation resolving the open questions in `File-Module-Structure-Proposal.md`.

## Summary of the call

Same phase-by-phase shape as the team's proposal (Monah \= ingestion, Sloane \= KPIs/anomalies, Matt \= API/dashboards), but with the four open questions resolved rather than left for later:

1. **No `src/` layer — flat top-level `medici/` package.** The `src/` layout is a real convention, but it typically requires an editable pip install (`pip install -e .`) or `PYTHONPATH` fiddling to import cleanly. For a beginner team integrating code for the first time on a one-week deadline, a flat package avoids that failure mode entirely — it works immediately when scripts are run from the repo root, and `pytest` auto-discovers it with zero config.  
     
2. **`medici-banking.py` gets renamed and moved — this isn't optional, it's a bug fix.** Python module names can't contain hyphens. `import medici-banking` is a syntax error. Since ingestion and transform need to import the `Account`/`Transaction`/`Ledger` classes from that file, it must become `medici/accounting.py` (renamed with an underscore, moved inside the package) before anyone can import from it.  
     
3. **`dashboards/` stays separate from the package**, matching the original proposal's reasoning — Streamlit apps are run directly (`streamlit run dashboards/branch_dashboard.py`), not imported like a module.  
     
4. **The legacy generator/demo scripts move to `scripts/`** — they're one-time data-generation and demo utilities, not code the pipeline imports from.  
     
5. **`contracts.py` uses Pydantic models, not plain dataclasses.** The Data-Contract Reference Sheet already specifies exact fields and types for `CleanedTransaction`, `KPIResult`, and `AlertRecord`. Since Matt's FastAPI layer needs Pydantic models for request/response validation anyway, defining the contracts as Pydantic models means one definition does double duty: it's the shared handshake *and* the API's validation schema. Recommend Sloane drafts this file first — Monah and Matt are both blocked on it.

## Recommended structure

MediciMessDelta/

├── medici/                          \# the shared package (flat — no src/)

│   ├── \_\_init\_\_.py

│   ├── accounting.py                \# renamed from medici-banking.py, moved here

│   ├── contracts.py                 \# Pydantic models — CleanedTransaction, KPIResult, AlertRecord

│   │

│   ├── ingestion/                   \# Monah — Phase 2

│   │   ├── \_\_init\_\_.py

│   │   ├── loaders.py               \# reads CSV & JSON into DataFrames

│   │   ├── validation.py            \# required-field checks, type conversion

│   │   └── dedup.py                 \# duplicate flagging, incremental "new rows only" loads

│   │

│   ├── transform/                   \# Sloane — Phase 3

│   │   ├── \_\_init\_\_.py

│   │   ├── clean.py                 \# normalize/clean fields post-ingestion

│   │   └── kpis.py                  \# every KPI formula (cash, deposits, loans, revenue, net income)

│   │

│   ├── anomaly/                     \# Sloane — Phase 4 & 8

│   │   ├── \_\_init\_\_.py

│   │   ├── rules.py                 \# Rules A–G (Benford's Law, duplicates, round numbers, etc.)

│   │   └── alerts.py                \# builds standardized alert records from rule hits

│   │

│   ├── storage/                     \# shared — where cleaned data / KPIs / alerts persist

│   │   ├── \_\_init\_\_.py

│   │   ├── db.py                    \# SQLite conn (alerts/flagged) \+ DuckDB conn (analytics)

│   │   └── models.py                \# table definitions (transactions, kpi\_results, alerts)

│   │

│   └── api/                         \# Matt — Phase 5

│       ├── \_\_init\_\_.py

│       ├── main.py                  \# FastAPI app entrypoint

│       ├── auth.py                  \# role-based access (branch manager vs. managing director)

│       └── routes/

│           ├── kpis.py

│           ├── transactions.py

│           ├── alerts.py

│           └── loans\_expenses.py

│

├── dashboards/                      \# Matt — Phases 6 & 7 (run directly, not imported)

│   ├── branch\_dashboard.py          \# Phase 6 — single-branch view

│   └── director\_dashboard.py        \# Phase 7 — network overview \+ access control

│

├── scripts/                         \# standalone utilities, not part of the pipeline

│   ├── validate\_transactions.py

│   ├── generate\_historical\_data.py

│   ├── generate\_additional\_data.py

│   ├── demo\_historical\_data.py

│   └── demo\_import\_export.py

│

├── notebooks/

│   ├── 01\_data\_exploration.ipynb    \# Monah — Phase 1

│   └── 08\_forensic\_exercise.ipynb   \# Sloane — Phase 8

│

├── tests/                           \# pytest — mirrors medici/ structure

│   ├── test\_ingestion.py

│   ├── test\_transform\_kpis.py

│   ├── test\_anomaly\_rules.py

│   ├── test\_api.py

│   └── test\_integration.py          \# full pipeline, end-to-end

│

├── data/

│   ├── raw/                         \# medici\_transactions.csv/.json — gitignored

│   └── processed/                   \# pipeline outputs — JSON/CSV

│

├── docs/                            \# existing specs, kept together

│   ├── DATA\_PIPELINE\_SPEC.md

│   ├── BRANCH\_OPS\_UI\_SPEC.md

│   ├── DATA\_CONTRACTS.md

│   ├── TRANSACTION\_DATA.md

│   ├── TECHNICAL\_NOTES.md

│   ├── SECURITY\_SUMMARY.md

│   └── diagrams/

│

├── requirements.txt

├── pyproject.toml

├── README.md

├── STUDENT\_GUIDE.md

├── PANDAS\_INTRO.md

├── LICENSE

└── .gitignore

## How this resolves the proposal's four open questions

| \# | Open question from the original proposal | Resolution here |
| :---- | :---- | :---- |
| 1 | `src/medici/` vs. flat top-level packages | Flat `medici/` package — no `src/` layer, avoids editable-install/`PYTHONPATH` friction for a beginner team |
| 2 | Where `dashboards/` lives | Stays separate at the top level, run directly with `streamlit run` |
| 3 | Do the legacy scripts move into `scripts/`, and where does `medici-banking.py` land? | Legacy generator/demo scripts → `scripts/`. The accounting engine is renamed `medici_banking.py` → `medici/accounting.py` (fixes a real import bug: hyphens aren't valid in Python module names) |
| 4 | Who owns `contracts.py` and how is it built | Sloane owns it, drafted first (Monah and Matt are both blocked on it), implemented as Pydantic models matching the Data-Contract Reference Sheet exactly |

