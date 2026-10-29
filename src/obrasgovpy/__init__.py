"""Access the 'ObrasGov' open data API from Python.

ObrasGov.br is the Brazilian federal government's platform for public
infrastructure projects. This package covers the open data API published at
``api-publica.obrasgov.gestao.gov.br/obras`` -- projects, physical execution,
contracts, budget commitments, geometries, feasibility studies and project
status histories::

    import obrasgovpy as og

    og.list_resources()
    og.list_filters("projects")

    og.get_projects(uf_principal="PE", page_size=10)
    og.get_contracts(id_projeto_investimento="134851.26-07")
    og.get_last_update()

Results are pandas DataFrames with typed date columns and one-to-many
relationships preserved as columns of lists; :func:`result_metadata` reports
the pagination totals the API gave. Filter names and categorical values are in
Portuguese because they belong to the API; an unknown filter name is an error
rather than a request.

This is the Python sibling of the R package `obrasgovr
<https://strategicprojects.github.io/obrasgovr/>`_; the two cover the same
ground with the same semantics.
"""

from __future__ import annotations

__version__ = "0.1.0"

from ._client import configure
from ._errors import FilterError, HTTPError, ObrasgovError, ResponseError
from .metadata import list_filters, list_resources
from .query import (
    MAX_PAGE_SIZE,
    get_commitments,
    get_contracts,
    get_feasibility_studies,
    get_geometries,
    get_last_update,
    get_physical_execution,
    get_projects,
    get_status_history,
    result_metadata,
)

__all__ = [
    "MAX_PAGE_SIZE",
    "FilterError",
    "HTTPError",
    "ObrasgovError",
    "ResponseError",
    "configure",
    "get_commitments",
    "get_contracts",
    "get_feasibility_studies",
    "get_geometries",
    "get_last_update",
    "get_physical_execution",
    "get_projects",
    "get_status_history",
    "list_filters",
    "list_resources",
    "result_metadata",
    "__version__",
]
