"""JSON records to DataFrame.

The API answers with an array of objects under ``data``, one per record, with
a JSON ``null`` wherever a field is missing. One-to-many relationships arrive
as arrays of objects and stay as ``object`` columns holding the lists as they
arrived; an empty array is still a relationship, just an empty one, and must
remain distinguishable from ``null``.
"""

from __future__ import annotations

import re

import pandas as pd

from ._errors import ResponseError

_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def to_frame(records: list, date_fields: list[str]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()

    for record in records:
        # A JSON ``{}`` would become a row of nothing and vanish in the
        # concatenation, leaving the result one record short of what the API
        # said it sent, with no error.
        if not isinstance(record, dict) or len(record) == 0:
            raise ResponseError("An API record has an unexpected format.")

    names = _record_names(records)
    columns = {
        name: [record.get(name) for record in records] for name in names
    }
    frame = pd.DataFrame(columns, columns=names)

    # The ``dt_``/``data_`` prefixes catch most date fields, but not all: the
    # API also names dates ``vigencia_*``. Fields the resource declares as
    # dates are typed too, so the result does not depend on naming luck.
    candidates = [
        name
        for name in names
        if name.startswith(("dt_", "data_")) or name in date_fields
    ]

    for name in candidates:
        frame[name] = _as_iso_date(frame[name], declared=name in date_fields)

    return frame


def _record_names(records: list) -> list[str]:
    """Every key seen, in the order the records present them.

    The column set comes from the response, not from this package, so a field
    added upstream still comes through.
    """
    names: dict[str, None] = {}
    for record in records:
        names.update(dict.fromkeys(record))
    return list(names)


def _as_iso_date(series: pd.Series, declared: bool) -> pd.Series:
    """Convert a column to dates, or leave it alone.

    The shape is checked with an anchored pattern *and* parsed with an explicit
    format. Neither alone is enough: inference errors on well-shaped impossible
    dates it should reject quietly, while a bare ``%Y-%m-%d`` parse would let
    ``"2026-01-02T03:04:05"`` silently lose its time. Conversion happens only
    when every present value passes both, so a column is never partly emptied.
    """
    present = series.notna()

    # A column whose values are all missing carries no evidence of its type.
    # When the resource declares it a date, type it from that declaration, so
    # the same field does not change dtype from page to page.
    if not present.any():
        return series.astype("datetime64[ns]") if declared else series

    values = series[present]
    if not all(isinstance(v, str) and _ISO_DATE.match(v) for v in values):
        return series

    parsed = pd.to_datetime(series, format="%Y-%m-%d", errors="coerce")
    if bool((present & parsed.isna()).any()):
        # Well-shaped but impossible, such as "2026-02-30": leave the column
        # as text rather than hide the bad value behind a NaT.
        return series

    return parsed.astype("datetime64[ns]")
