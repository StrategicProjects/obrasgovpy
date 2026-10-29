"""Opt-in integration tests against the real API.

Run with ``OBRASGOVPY_LIVE_TESTS=true pytest tests/test_live.py``. They are
skipped everywhere else so the suite stays offline.
"""

from __future__ import annotations

import datetime as dt
import os

import pandas as pd
import pytest

import obrasgovpy as og

live = pytest.mark.skipif(
    os.environ.get("OBRASGOVPY_LIVE_TESTS", "").lower() != "true",
    reason="Set OBRASGOVPY_LIVE_TESTS=true to run integration tests",
)


@live
def test_the_official_api_reports_its_update_timestamp():
    value = og.get_last_update()

    assert value.tzinfo is not None
    assert value > dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)


@live
def test_projects_come_back_typed_and_paginated():
    frame = og.get_projects(uf_principal="PE", page_size=5)
    meta = og.result_metadata(frame)

    assert len(frame) == 5
    assert pd.api.types.is_datetime64_any_dtype(frame["dt_cadastro"])
    assert isinstance(frame["executores"].iloc[0], list)
    assert meta["total_items"] >= len(frame)
    assert set(frame["uf_principal"]) == {"PE"}


@live
def test_enum_values_filter_real_data():
    frame = og.get_contracts(categoria_contrato="Serviços de Engenharia", page_size=2)

    assert len(frame) == 2
    assert set(frame["categoria_contrato"]) == {"Serviços de Engenharia"}
