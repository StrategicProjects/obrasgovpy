"""The query verbs: one ``get_*`` function per resource, plus
:func:`get_last_update` and :func:`result_metadata`."""

from __future__ import annotations

import datetime as _dt
import math
import re

import pandas as pd

from . import _client, _parse, metadata
from ._errors import FilterError, ResponseError

__all__ = [
    "get_projects",
    "get_commitments",
    "get_physical_execution",
    "get_contracts",
    "get_geometries",
    "get_status_history",
    "get_feasibility_studies",
    "get_last_update",
    "result_metadata",
    "MAX_PAGE_SIZE",
]

#: The largest page the API serves.
MAX_PAGE_SIZE = 200

_METADATA_ATTR = "obrasgovpy"


def result_metadata(frame: pd.DataFrame) -> dict | None:
    """Pagination metadata of a DataFrame returned by a ``get_*`` function.

    A dict with the resource, the totals the API reported, the first page and
    how many pages were retrieved; ``None`` for other objects.
    """
    try:
        return frame.attrs.get(_METADATA_ATTR)
    except AttributeError:
        return None


def _get_paginated(
    resource: str,
    filters: dict,
    page: int,
    page_size: int,
    all_pages: bool,
    page_limit: float,
    base_url: str | None,
) -> pd.DataFrame:
    resource = metadata.match_resource(resource)
    meta = metadata.RESOURCES[resource]

    params = _validate_filters(filters, meta["filters"])
    page = _check_positive_integer(page, "page")
    page_size = _check_positive_integer(page_size, "page_size")
    if page_size > MAX_PAGE_SIZE:
        raise ValueError(f"page_size cannot be greater than {MAX_PAGE_SIZE}.")
    if not isinstance(all_pages, bool):
        raise ValueError("all_pages must be True or False.")
    page_limit = _check_page_limit(page_limit)

    bodies = _collect_pages(
        meta["endpoint"], params, page, page_size, all_pages, page_limit, base_url
    )

    records = [record for body in bodies for record in body["data"]]
    frame = _parse.to_frame(records, metadata.date_fields(resource))

    frame.attrs[_METADATA_ATTR] = {
        "resource": resource,
        "endpoint": meta["endpoint"],
        "total_pages": _client.response_total(bodies[0], "total_pages"),
        "total_items": _client.response_total(bodies[0], "total_items"),
        "first_page": page,
        "pages_retrieved": len(bodies),
        "page_size": page_size,
        "retrieved_at": _dt.datetime.now(_dt.timezone.utc),
    }
    return frame


def _collect_pages(
    endpoint: str,
    params: list,
    page: int,
    page_size: int,
    all_pages: bool,
    page_limit: float,
    base_url: str | None,
) -> list[dict]:
    first = _client.fetch_page(endpoint, params, page, page_size, base_url)
    total_pages = _client.response_total(first, "total_pages")
    _client.check_totals_consistent(first, total_pages)
    bodies = [first]

    if not all_pages or total_pages <= page:
        return bodies

    last_page = total_pages
    if math.isfinite(page_limit):
        last_page = min(last_page, page + int(page_limit) - 1)

    # An exhausted budget must return here rather than build an empty or
    # descending page range.
    if last_page <= page:
        return bodies

    for next_page in range(page + 1, last_page + 1):
        bodies.append(
            _client.fetch_page(endpoint, params, next_page, page_size, base_url)
        )

    return bodies


def _validate_filters(filters: dict, allowed: dict) -> list[tuple[str, str]]:
    unknown = set(filters) - set(allowed)
    if unknown:
        names = ", ".join(sorted(unknown))
        raise FilterError(
            f"Unknown filter(s): {names}. See the available filters with "
            "list_filters()."
        )

    params = []
    for name, value in filters.items():
        if value is None:
            continue
        if isinstance(value, (list, tuple, set, dict)):
            raise FilterError(f"Filter {name!r} must contain one value.")
        if isinstance(value, float) and math.isnan(value):
            raise FilterError(f"Filter {name!r} must contain one non-missing value.")
        if isinstance(value, (_dt.date, _dt.datetime)):
            value = value.strftime("%Y-%m-%d")
        elif isinstance(value, bool):
            raise FilterError(f"Filter {name!r} must contain one value, not a bool.")
        params.append((name, str(value)))

    return params


def _check_positive_integer(value, argument: str) -> int:
    usable = (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(value)
        and float(value) == int(value)
        and value >= 1
    )
    if not usable:
        raise ValueError(f"{argument} must be a positive integer.")
    return int(value)


def _check_page_limit(value) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("page_limit must be a positive integer or math.inf.")
    if math.isinf(value) and value > 0:
        return float(value)
    if math.isnan(value) or value < 1 or float(value) != int(value):
        raise ValueError("page_limit must be a positive integer or math.inf.")
    return float(value)


def get_projects(
    *,
    page: int = 1,
    page_size: int = 50,
    all_pages: bool = False,
    page_limit: float = math.inf,
    base_url: str | None = None,
    **filters,
) -> pd.DataFrame:
    """Retrieve infrastructure projects.

    Projects carry their nested relationships -- executors, recipients,
    funding sources, policy areas and point geometries -- as columns of lists.

    Filters
    -------
    Name each filter after one of the resource's query parameters::

        og.get_projects(uf_principal="PE", situacao="Em execução")

    See them all with ``list_filters("projects")``. Filter names and
    categorical values are in Portuguese because they belong to the API.

    Pagination
    ----------
    ``page`` is the first page to retrieve, starting at 1, and ``page_size``
    the records per page, between 1 and 200. With ``all_pages=True``,
    successive pages are retrieved starting at ``page``, up to ``page_limit``
    pages in all (``math.inf``, the default limit, means every page).

    Returns
    -------
    pandas.DataFrame
        One row per record. One-to-many relationships are preserved in
        columns of lists. :func:`result_metadata` reports the totals the API
        gave and how many pages were fetched.
    """
    return _get_paginated(
        "projects", filters, page, page_size, all_pages, page_limit, base_url
    )


def get_commitments(
    *,
    page: int = 1,
    page_size: int = 50,
    all_pages: bool = False,
    page_limit: float = math.inf,
    base_url: str | None = None,
    **filters,
) -> pd.DataFrame:
    """Retrieve budget commitments and financial execution amounts.

    See ``list_filters("commitments")`` for the filters, and
    :func:`get_projects` for the pagination arguments.
    """
    return _get_paginated(
        "commitments", filters, page, page_size, all_pages, page_limit, base_url
    )


def get_physical_execution(
    *,
    page: int = 1,
    page_size: int = 50,
    all_pages: bool = False,
    page_limit: float = math.inf,
    base_url: str | None = None,
    **filters,
) -> pd.DataFrame:
    """Retrieve physical execution data: percentages, instruments and dates.

    See ``list_filters("physical_execution")`` for the filters, and
    :func:`get_projects` for the pagination arguments.
    """
    return _get_paginated(
        "physical_execution", filters, page, page_size, all_pages, page_limit, base_url
    )


def get_contracts(
    *,
    page: int = 1,
    page_size: int = 50,
    all_pages: bool = False,
    page_limit: float = math.inf,
    base_url: str | None = None,
    **filters,
) -> pd.DataFrame:
    """Retrieve contracts linked to infrastructure projects.

    See ``list_filters("contracts")`` for the filters, and
    :func:`get_projects` for the pagination arguments.
    """
    return _get_paginated(
        "contracts", filters, page, page_size, all_pages, page_limit, base_url
    )


def get_geometries(
    *,
    page: int = 1,
    page_size: int = 50,
    all_pages: bool = False,
    page_limit: float = math.inf,
    base_url: str | None = None,
    **filters,
) -> pd.DataFrame:
    """Retrieve geometries and territorial identifiers.

    See ``list_filters("geometries")`` for the filters, and
    :func:`get_projects` for the pagination arguments.
    """
    return _get_paginated(
        "geometries", filters, page, page_size, all_pages, page_limit, base_url
    )


def get_status_history(
    *,
    page: int = 1,
    page_size: int = 50,
    all_pages: bool = False,
    page_limit: float = math.inf,
    base_url: str | None = None,
    **filters,
) -> pd.DataFrame:
    """Retrieve the histories of cancelled or suspended projects.

    Includes reasons and remedial actions. See
    ``list_filters("status_history")`` for the filters, and
    :func:`get_projects` for the pagination arguments.
    """
    return _get_paginated(
        "status_history", filters, page, page_size, all_pages, page_limit, base_url
    )


def get_feasibility_studies(
    *,
    page: int = 1,
    page_size: int = 50,
    all_pages: bool = False,
    page_limit: float = math.inf,
    base_url: str | None = None,
    **filters,
) -> pd.DataFrame:
    """Retrieve feasibility studies linked to projects.

    See ``list_filters("feasibility_studies")`` for the filters, and
    :func:`get_projects` for the pagination arguments.
    """
    return _get_paginated(
        "feasibility_studies", filters, page, page_size, all_pages, page_limit, base_url
    )


_TIMESTAMP = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:?\d{2})?$"
)


def get_last_update(base_url: str | None = None) -> _dt.datetime:
    """The timestamp of the API's last data update, as an aware UTC datetime."""
    body = _client.perform("data-atualizacao", [], base_url)
    value = body.get("data_ultima_atualizacao") if isinstance(body, dict) else None

    if not isinstance(value, str):
        raise ResponseError("The data update response has an unexpected format.")

    return _parse_timestamp(value)


def _parse_timestamp(value: str) -> _dt.datetime:
    # The whole string is validated before parsing, so trailing text or a
    # truncated offset is an error rather than a silently misread timestamp.
    if not _TIMESTAMP.match(value):
        raise ResponseError(
            f"The data update response has an unparseable timestamp: {value!r}."
        )

    # ``fromisoformat`` before Python 3.11 takes neither ``Z`` nor an offset
    # written without a colon, so both are normalized first.
    normalized = re.sub(r"Z$", "+00:00", value)
    normalized = re.sub(r"([+-]\d{2})(\d{2})$", r"\1:\2", normalized)

    try:
        parsed = _dt.datetime.fromisoformat(normalized)
    except ValueError as error:
        # Well shaped but impossible, such as "2026-02-30T00:00:00".
        raise ResponseError(
            f"The data update response has an unparseable timestamp: {value!r}."
        ) from error

    # The API reports naive UTC; a value carrying an offset is converted
    # rather than read as UTC.
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=_dt.timezone.utc)
    return parsed.astimezone(_dt.timezone.utc)
