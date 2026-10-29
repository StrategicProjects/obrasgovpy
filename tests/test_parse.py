"""Records to DataFrame: date typing, nested relationships and malformed input."""

from __future__ import annotations

import json

import pandas as pd
import pytest

import obrasgovpy as og
from obrasgovpy._errors import ResponseError
from tests.conftest import add_page, envelope, page_body


def test_date_columns_are_typed(mock):
    add_page(mock, page_body(2))

    frame = og.get_projects()

    assert pd.api.types.is_datetime64_any_dtype(frame["dt_cadastro"])
    assert frame["dt_cadastro"].iloc[0] == pd.Timestamp("2025-01-01")


def test_declared_date_columns_stay_dates_when_all_null(mock):
    # A column of nothing carries no evidence of its type: it must be typed
    # from the resource metadata, or the same field changes dtype from page to
    # page.
    add_page(mock, page_body(2))

    frame = og.get_projects()

    assert pd.api.types.is_datetime64_any_dtype(frame["dt_final_efetiva"])
    assert frame["dt_final_efetiva"].isna().all()


def test_a_malformed_date_leaves_the_whole_column_as_text(mock):
    rows = json.dumps(
        [
            {"id_projeto_investimento": "1", "dt_cadastro": "2025-01-01"},
            {"id_projeto_investimento": "2", "dt_cadastro": "2026-02-30"},
        ]
    )
    add_page(mock, envelope(rows, total=2))

    frame = og.get_projects()

    # "2026-02-30" is well shaped but impossible. Parsing around it would
    # empty it into NaT and hide the bad value; the column stays text instead.
    assert not pd.api.types.is_datetime64_any_dtype(frame["dt_cadastro"])
    assert frame["dt_cadastro"].tolist() == ["2025-01-01", "2026-02-30"]


def test_a_datetime_string_is_not_silently_truncated_to_a_date(mock):
    rows = json.dumps(
        [{"id_projeto_investimento": "1", "dt_cadastro": "2025-01-02T03:04:05"}]
    )
    add_page(mock, envelope(rows, total=1))

    frame = og.get_projects()

    assert frame["dt_cadastro"].tolist() == ["2025-01-02T03:04:05"]


def test_nested_relationships_stay_as_lists(mock):
    add_page(mock, page_body(1))

    frame = og.get_projects()

    assert frame["tomadores"].iloc[0] == [{"nome": "Prefeitura", "codigo": 1}]
    # An empty array is still a relationship, just an empty one. It must stay
    # a list, or it becomes indistinguishable from null.
    assert frame["executores"].iloc[0] == []


def test_fields_missing_from_some_records_become_null(mock):
    rows = json.dumps(
        [
            {"id_projeto_investimento": "1", "desc_nome": "Obra 1"},
            {"id_projeto_investimento": "2"},
        ]
    )
    add_page(mock, envelope(rows, total=2))

    frame = og.get_projects()

    assert frame["desc_nome"].tolist()[0] == "Obra 1"
    assert pd.isna(frame["desc_nome"].iloc[1])


def test_an_empty_record_is_an_error_not_a_lost_row(mock):
    # A JSON {} would otherwise vanish in the concatenation, leaving the
    # result one record short of what the API said it sent, with no error.
    add_page(mock, envelope('[{"id_projeto_investimento":"1"},{}]', total=2))

    with pytest.raises(ResponseError, match="unexpected format"):
        og.get_projects()


def test_a_non_object_record_is_an_error(mock):
    add_page(mock, envelope('[42]', total=1))

    with pytest.raises(ResponseError, match="unexpected format"):
        og.get_projects()


def test_an_empty_result_is_an_empty_frame(mock):
    add_page(mock, envelope("[]", total=0))

    frame = og.get_projects()

    assert isinstance(frame, pd.DataFrame)
    assert len(frame) == 0


def test_last_update_returns_an_aware_utc_datetime(mock):
    add_page(
        mock,
        '{"data_ultima_atualizacao":"2026-10-28T03:04:05"}',
        endpoint="data-atualizacao",
    )

    value = og.get_last_update()

    assert value.isoformat() == "2026-10-28T03:04:05+00:00"


def test_last_update_converts_offsets_instead_of_reading_them_as_utc(mock):
    add_page(
        mock,
        '{"data_ultima_atualizacao":"2026-10-28T00:00:00-03:00"}',
        endpoint="data-atualizacao",
    )

    value = og.get_last_update()

    assert value.isoformat() == "2026-10-28T03:00:00+00:00"


@pytest.mark.parametrize(
    "timestamp",
    [
        "2026-10-28T00:00:00junk",  # trailing text strptime would ignore
        "2026-10-28T00:00:00-03",  # truncated offset
        "2026-02-30T00:00:00",  # well shaped but impossible
        "28/10/2026 00:00",
    ],
)
def test_last_update_rejects_unparseable_timestamps(mock, timestamp):
    add_page(
        mock,
        json.dumps({"data_ultima_atualizacao": timestamp}),
        endpoint="data-atualizacao",
    )

    with pytest.raises(ResponseError, match="unparseable timestamp"):
        og.get_last_update()


def test_last_update_rejects_a_missing_field(mock):
    add_page(mock, "{}", endpoint="data-atualizacao")

    with pytest.raises(ResponseError, match="unexpected format"):
        og.get_last_update()
