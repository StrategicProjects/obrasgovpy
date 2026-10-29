# obrasgovpy

Python client for the ObrasGov open data API at
`https://api-publica.obrasgov.gestao.gov.br/obras`. The sibling of
`../obrasgovr`, which covers the same ground in R (on CRAN since 2026-07-24).

## Keep the two packages in step

Both freeze the same OpenAPI contract: 8 resources, the same filter names and
types, and the same enumerated values. `test_metadata.py` asserts the per-
resource filter counts against the R sibling. When the contract changes,
change both packages, and port new defenses both ways.

## The R sibling's lessons apply here verbatim

obrasgovr's CLAUDE.md documents twenty real defects that passed a green
check. The ones ported into this package's design, each with a test proven
against a deliberately broken implementation (mutation testing — run it when
touching `_client.py`, `_parse.py` or `query.py`):

- The response's `page_number` echo is checked against the page requested; a
  proxy answering page 2 with page 1 must error, not duplicate.
- Pagination totals are validated before they are trusted, **including when
  the payload is empty** — with no records, the totals-consistency check has
  nothing to contradict, so `response_total` is the only defense.
- The page range never duplicates or counts backwards on `page_limit=1`.
- Dates parse all-or-nothing per column: an impossible "2026-02-30" leaves
  the whole column as text; a datetime string is never truncated to a date.
- Empty JSON `{}` records error rather than silently vanishing from the
  row count.
- Timestamps are validated whole before parsing (trailing text, truncated
  offsets).

## Conventions

- House template is `../transferegovpy` (hatchling, src layout, requests +
  pandas, responses for mocks, ruff line-length 100).
- Tests build responses from literal JSON wherever nulls matter.
- Run before committing: `pytest`, `ruff check src tests`.
- Live tests: `OBRASGOVPY_LIVE_TESTS=true pytest tests/test_live.py`.
- Publishing: GitHub release → `publish.yaml` → PyPI Trusted Publishing
  (environment `pypi`). No API token is stored anywhere.
