# Changelog

## 0.1.0

First release: a pandas-friendly client for the ObrasGov open data API,
sibling of the R package [obrasgovr](https://strategicprojects.github.io/obrasgovr/).

- One function per resource: `get_projects`, `get_commitments`,
  `get_physical_execution`, `get_contracts`, `get_geometries`,
  `get_status_history`, `get_feasibility_studies` and `get_last_update`.
- Resource and filter discovery with `list_resources()` and `list_filters()`,
  including the enumerated values the OpenAPI contract declares.
- Defensive multi-page collection: validated pagination totals, a page-echo
  check against silent duplication, and totals-consistency checks against
  silent truncation.
- Typed date columns (strict, all-or-nothing parsing), nested relationships
  preserved as columns of lists, request throttling (60/min) and transient
  retries with backoff.
