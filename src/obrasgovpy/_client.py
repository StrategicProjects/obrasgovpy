"""HTTP transport: throttling, retries, error reporting and envelope checks.

The API is a FastAPI service. A resource query is a GET on the endpoint,
filters are typed query parameters, and the answer is an envelope carrying the
records under ``data`` alongside the pagination state.
"""

from __future__ import annotations

import random
import threading
import time
from collections.abc import Sequence

import requests

from ._errors import HTTPError, ResponseError

DEFAULT_BASE_URL = "https://api-publica.obrasgov.gestao.gov.br/obras"

# Only these are worth retrying. A 422 is the service rejecting the query
# itself and will fail identically every time.
TRANSIENT = frozenset({429, 500, 502, 503, 504})

_config = {
    "base_url": None,
    "timeout": 30.0,
    "max_tries": 4,
    "requests_per_minute": 60.0,
}

_throttle_lock = threading.Lock()
_last_request = [0.0]

_session_lock = threading.Lock()
_session: requests.Session | None = None


def configure(**options) -> dict:
    """Set connection options for the session, or read them back.

    The options are ``base_url``, ``timeout`` (seconds), ``max_tries`` and
    ``requests_per_minute``. Calling with no arguments reads the current
    configuration back without changing it.
    """
    unknown = set(options) - set(_config)
    if unknown:
        raise ValueError(f"Unknown option(s): {', '.join(sorted(unknown))}.")
    _config.update(options)
    return dict(_config)


def base_url() -> str:
    return _config["base_url"] or DEFAULT_BASE_URL


def check_base_url(url: str) -> str:
    if not isinstance(url, str) or not url.startswith("https://"):
        raise ValueError("base_url must be a single HTTPS URL.")
    return url


def _user_agent() -> str:
    from . import __version__

    return f"obrasgovpy/{__version__} (https://github.com/StrategicProjects/obrasgovpy)"


def session() -> requests.Session:
    global _session
    with _session_lock:
        if _session is None:
            _session = requests.Session()
            _session.headers.update(
                {"Accept": "application/json", "User-Agent": _user_agent()}
            )
        return _session


def _wait_turn() -> None:
    """Keep the package a considerate client of a public service."""
    rate = float(_config["requests_per_minute"])
    if rate <= 0:
        return

    interval = 60.0 / rate
    with _throttle_lock:
        elapsed = time.monotonic() - _last_request[0]
        if elapsed < interval:
            time.sleep(interval - elapsed)
        _last_request[0] = time.monotonic()


def build_url(endpoint: str, url: str) -> str:
    return f"{url.rstrip('/')}/{endpoint.lstrip('/')}"


def perform(endpoint: str, params: Sequence[tuple[str, str]], url: str | None = None):
    """One request, returning the parsed JSON body."""
    target = check_base_url(url or base_url())
    prepared = requests.Request(
        "GET", build_url(endpoint, target), params=list(params)
    ).prepare()
    return _perform(prepared.url)


def _perform(url: str):
    last_error: Exception | None = None
    max_tries = int(_config["max_tries"])

    for attempt in range(1, max_tries + 1):
        _wait_turn()

        try:
            response = session().get(url, timeout=_config["timeout"])
        except requests.RequestException as error:  # connection, DNS, timeout
            last_error = error
            if attempt == max_tries:
                raise ResponseError(
                    f"The request to the ObrasGov API failed: {error}"
                ) from error
            _backoff(attempt)
            continue

        if response.status_code in TRANSIENT and attempt < max_tries:
            _backoff(attempt, response)
            continue

        _raise_for_status(response)
        return _body(response)

    raise ResponseError(f"The request to the ObrasGov API failed: {last_error}")


def _backoff(attempt: int, response: requests.Response | None = None) -> None:
    if response is not None:
        after = response.headers.get("Retry-After")
        if after and after.isdigit():
            time.sleep(min(60, int(after)))
            return

    time.sleep(min(60.0, 2.0**attempt) * random.uniform(0.5, 1.5))


def _raise_for_status(response: requests.Response) -> None:
    if response.status_code < 400:
        return

    detail = _details(response)
    message = f"The ObrasGov API returned HTTP {response.status_code} ({response.reason})."
    for line in detail:
        message += f" {line}"

    raise HTTPError(message, status=response.status_code, detail=detail)


def _details(response: requests.Response) -> list[str]:
    """FastAPI reports a rejected query under ``detail``.

    That is a list of validation objects for a 422, each naming the offending
    parameter under ``loc``, and a bare string otherwise.
    """
    try:
        body = response.json()
    except ValueError:
        return []

    # A JSON body need not be an object: indexing an atomic value would error
    # and mask the HTTP status being reported.
    if not isinstance(body, dict) or "detail" not in body:
        return []

    detail = body["detail"]
    if isinstance(detail, str):
        return [detail] if detail else []
    if not isinstance(detail, list):
        return []

    lines = []
    for item in detail:
        if not isinstance(item, dict):
            continue
        message = item.get("msg")
        if not isinstance(message, str):
            continue
        where = [str(p) for p in item.get("loc", []) if p != "query"]
        lines.append(f"{'.'.join(where)}: {message}" if where else message)
    return lines


def _body(response: requests.Response):
    try:
        return response.json()
    except ValueError as error:
        raise ResponseError(
            "The ObrasGov API returned a body that is not valid JSON."
        ) from error


def fetch_page(
    endpoint: str,
    params: Sequence[tuple[str, str]],
    page: int,
    page_size: int,
    url: str | None = None,
) -> dict:
    """One page of a paginated resource, as the validated envelope."""
    query = list(params) + [
        ("pagina", str(int(page))),
        ("tamanho_da_pagina", str(int(page_size))),
    ]
    body = perform(endpoint, query, url)

    if not isinstance(body, dict) or not isinstance(body.get("data"), list):
        raise ResponseError("The paginated API response has an unexpected format.")

    # The response says which page it is. Without checking, a server or proxy
    # that answers page 2 with page 1 would be silently collected as if it were
    # new data, duplicating records under the guise of a complete result. A
    # marker that is present must be usable: a string "1" or a fractional 1.9
    # must be an error, not a pass.
    returned = body.get("page_number")
    if returned is not None:
        if not _usable_page_marker(returned):
            raise ResponseError("The API reported an unusable page_number.")
        if int(returned) != int(page):
            raise ResponseError(
                f"The API returned page {int(returned)} when page {int(page)} was "
                "requested. Collecting it would duplicate records."
            )

    return body


def _usable_page_marker(value) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return float(value) == int(value) and abs(float(value)) < float("inf")


def response_total(body: dict, field: str) -> int:
    """A pagination total, validated.

    Totals drive multi-page collection, so a missing one must abort rather
    than default to zero: that would silently stop after the first page and
    report the truncated result as complete. Fractional, infinite and negative
    totals are rejected for the same reason.
    """
    value = body.get(field)

    usable = (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and float(value) == int(value)
        and value >= 0
        and abs(float(value)) < float("inf")
    )
    if not usable:
        raise ResponseError(
            f"The API response has no usable {field}; pagination cannot be "
            "verified, so the result may be incomplete."
        )

    return int(value)


def check_totals_consistent(body: dict, total_pages: int) -> None:
    """Reject a zero total that contradicts the payload.

    Zero is a legitimate total for an empty result, but ``total_pages = 0``
    alongside records would stop collection on the first page and present the
    truncated result as complete -- the same silent-incompleteness class as a
    missing total, reached through a bad zero.
    """
    total_items = response_total(body, "total_items")
    records = len(body["data"])

    inconsistent = (total_pages == 0 and (records > 0 or total_items > 0)) or (
        total_items == 0 and records > 0
    )

    if inconsistent:
        raise ResponseError(
            "The API reported pagination totals that contradict the response: "
            f"got {records} record(s) with total_pages = {total_pages} and "
            f"total_items = {total_items}. Pagination cannot be verified, so "
            "the result may be incomplete."
        )
