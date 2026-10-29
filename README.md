# obrasgovpy

[![PyPI](https://img.shields.io/pypi/v/obrasgovpy.svg)](https://pypi.org/project/obrasgovpy/)
[![Python](https://img.shields.io/pypi/pyversions/obrasgovpy.svg)](https://pypi.org/project/obrasgovpy/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Access the open data API of **ObrasGov.br**, the Brazilian federal
government's platform for public infrastructure projects, from Python.

This is the Python sibling of
[obrasgovr](https://strategicprojects.github.io/obrasgovr/); the two cover the
same ground with the same semantics.

## What this package covers

The package targets the public API at
`api-publica.obrasgov.gestao.gov.br/obras`
([documentation](https://api-publica.obrasgov.gestao.gov.br/obras/docs)),
which publishes eight resources:

| Function | Resource | Endpoint |
|---|---|---|
| `get_projects()` | Infrastructure projects, with executors, recipients, funding sources, policy areas and geometries nested | `projeto-investimento` |
| `get_commitments()` | Budget commitments and financial execution amounts | `empenho` |
| `get_physical_execution()` | Physical execution percentages, instruments and dates | `execucao-fisica` |
| `get_contracts()` | Contracts linked to projects | `contrato` |
| `get_geometries()` | Geometries and territorial identifiers | `geometria` |
| `get_status_history()` | Histories of cancelled or suspended projects | `historico-situacao-cancelada-paralisada` |
| `get_feasibility_studies()` | Feasibility studies linked to projects | `estudo-viabilidade` |
| `get_last_update()` | The timestamp of the API's last data update | `data-atualizacao` |

## Installation

```bash
pip install obrasgovpy
```

## Getting started

```python
import obrasgovpy as og

og.list_resources()
og.list_filters("projects")

projects = og.get_projects(uf_principal="PE", situacao="Em execução", page_size=50)
contracts = og.get_contracts(id_projeto_investimento="134851.26-07")

og.get_last_update()
```

Results are pandas DataFrames. Date columns arrive typed as datetimes, and
one-to-many relationships are preserved as columns of lists. The totals the
API reported, and how many pages were fetched, travel with the result:

```python
og.result_metadata(projects)
```

Filter names and categorical values are in Portuguese because they belong to
the API. An unknown filter name is an error rather than a request, so a typo
cannot return plausible, wrong data. `list_filters()` shows each resource's
filters, their types and, for the enumerated ones, the permitted values.

## Pagination

Each request returns one page of at most 200 records. `page` is the first
page to retrieve and `page_size` the records per page; with `all_pages=True`,
successive pages are collected starting at `page`:

```python
import math

everything = og.get_projects(
    uf_principal="PE",
    page_size=200,
    all_pages=True,
    page_limit=math.inf,  # the default: every page
)
```

Multi-page collection is defensive by design: the page number each response
reports is checked against the page requested, the pagination totals are
validated before they are trusted, and totals that contradict the payload are
an error rather than a silently truncated result. Requests are throttled to
60 per minute and transient failures are retried with backoff; tune both with
`og.configure()`.

## The previous ObrasGov API

This package exclusively uses the current environment. The previous ObrasGov
API is not supported: ObrasGov set 31 August 2026 as the deadline for
migrating away from it, and that deadline has passed.

## Releasing (maintainers)

Publishing uses PyPI
[Trusted Publishing](https://docs.pypi.org/trusted-publishers/): the
`publish.yaml` workflow builds and uploads when a GitHub release is published.
Register the publisher on PyPI with repository owner `StrategicProjects`,
repository `obrasgovpy`, workflow `publish.yaml` and environment `pypi`.

## License

MIT. See [LICENSE](LICENSE).
