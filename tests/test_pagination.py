"""Multi-page collection and its defenses.

Every check here exists because its absence has a quiet failure mode: a
duplicated page, a truncated result presented as complete, or a page range
built backwards.
"""

from __future__ import annotations

import math

import pytest

import obrasgovpy as og
from obrasgovpy._errors import ResponseError
from tests.conftest import add_page, page_body


def test_a_single_page_is_returned_as_is(mock):
    add_page(mock, page_body(3))

    frame = og.get_projects()

    assert len(frame) == 3
    assert len(mock.calls) == 1


def test_all_pages_collects_every_page(mock):
    add_page(mock, page_body(2, start=1, total=5, page=1, page_size=2))
    add_page(mock, page_body(2, start=3, total=5, page=2, page_size=2))
    add_page(mock, page_body(1, start=5, total=5, page=3, page_size=2))

    frame = og.get_projects(page_size=2, all_pages=True)

    assert len(frame) == 5
    assert frame["id_projeto_investimento"].is_unique
    assert len(mock.calls) == 3


def test_page_limit_bounds_the_collection(mock):
    add_page(mock, page_body(2, start=1, total=6, page=1, page_size=2))
    add_page(mock, page_body(2, start=3, total=6, page=2, page_size=2))

    frame = og.get_projects(page_size=2, all_pages=True, page_limit=2)

    assert len(frame) == 4
    assert len(mock.calls) == 2


def test_page_limit_of_one_fetches_exactly_one_page(mock):
    # This duplicated data once in the R sibling: an exhausted budget built a
    # backwards page range instead of stopping.
    add_page(mock, page_body(2, start=1, total=6, page=1, page_size=2))

    frame = og.get_projects(page_size=2, all_pages=True, page_limit=1)

    assert len(frame) == 2
    assert frame["id_projeto_investimento"].is_unique
    assert len(mock.calls) == 1


def test_collection_can_start_past_the_first_page(mock):
    add_page(mock, page_body(2, start=3, total=6, page=2, page_size=2))
    add_page(mock, page_body(2, start=5, total=6, page=3, page_size=2))

    frame = og.get_projects(page=2, page_size=2, all_pages=True)

    assert len(frame) == 4
    assert len(mock.calls) == 2


def test_a_wrong_page_echo_is_rejected(mock):
    # A proxy that answers page 2 with page 1 again must be an error, not a
    # silent duplication.
    add_page(mock, page_body(2, start=1, total=4, page=1, page_size=2))
    add_page(mock, page_body(2, start=1, total=4, page=1, page_size=2))

    with pytest.raises(ResponseError, match="page 1 when page 2"):
        og.get_projects(page_size=2, all_pages=True)


def test_an_unusable_page_echo_is_rejected(mock):
    body = page_body(1).replace('"page_number":1', '"page_number":"1"')
    add_page(mock, body)

    with pytest.raises(ResponseError, match="unusable page_number"):
        og.get_projects()


def test_a_fractional_page_echo_is_rejected(mock):
    body = page_body(1).replace('"page_number":1', '"page_number":1.9')
    add_page(mock, body)

    with pytest.raises(ResponseError, match="unusable page_number"):
        og.get_projects()


def test_a_missing_total_is_an_error_not_a_truncation(mock):
    body = (
        '{"data":[{"id_projeto_investimento":"1"}],'
        '"total_items":1,"page_number":1,"page_size":50}'
    )
    add_page(mock, body)

    with pytest.raises(ResponseError, match="total_pages"):
        og.get_projects()


def test_a_fractional_total_is_rejected(mock):
    body = page_body(1).replace('"total_pages":1', '"total_pages":1.5')
    add_page(mock, body)

    with pytest.raises(ResponseError, match="total_pages"):
        og.get_projects()


def test_totals_that_contradict_the_payload_are_rejected(mock):
    # total_pages = 0 alongside records would stop collection on the first
    # page and present the truncated result as complete.
    add_page(mock, page_body(2, total=2, pages=0))

    with pytest.raises(ResponseError, match="contradict"):
        og.get_projects(all_pages=True)


def test_zero_totals_with_an_empty_payload_are_legitimate(mock):
    add_page(mock, '{"data":[],"total_pages":0,"total_items":0,'
                   '"page_number":1,"page_size":50}')

    frame = og.get_projects()

    assert len(frame) == 0


def test_result_metadata_reports_the_collection(mock):
    add_page(mock, page_body(2, start=1, total=4, page=1, page_size=2))
    add_page(mock, page_body(2, start=3, total=4, page=2, page_size=2))

    frame = og.get_projects(page_size=2, all_pages=True)
    meta = og.result_metadata(frame)

    assert meta["resource"] == "projects"
    assert meta["endpoint"] == "projeto-investimento"
    assert meta["total_pages"] == 2
    assert meta["total_items"] == 4
    assert meta["first_page"] == 1
    assert meta["pages_retrieved"] == 2
    assert meta["page_size"] == 2


def test_result_metadata_is_none_elsewhere():
    assert og.result_metadata("not a frame") is None


@pytest.mark.parametrize("page", [0, -1, 1.5, math.inf, math.nan, "1", True])
def test_bad_pages_are_rejected(page):
    with pytest.raises(ValueError, match="page"):
        og.get_projects(page=page)


@pytest.mark.parametrize("page_size", [0, -1, 2.5, 201, math.inf, "50", True])
def test_bad_page_sizes_are_rejected(page_size):
    with pytest.raises(ValueError, match="page_size"):
        og.get_projects(page_size=page_size)


@pytest.mark.parametrize("all_pages", ["yes", 1, None])
def test_all_pages_must_be_a_bool(all_pages):
    with pytest.raises(ValueError, match="all_pages"):
        og.get_projects(all_pages=all_pages)


@pytest.mark.parametrize("page_limit", [0, -1, 1.5, math.nan, -math.inf, "2", True])
def test_bad_page_limits_are_rejected(page_limit):
    with pytest.raises(ValueError, match="page_limit"):
        og.get_projects(page_limit=page_limit)


def test_pagination_parameters_are_sent_in_portuguese(mock):
    add_page(mock, page_body(1, page=3, page_size=10))

    og.get_projects(page=3, page_size=10)

    url = mock.calls[0].request.url
    assert "pagina=3" in url
    assert "tamanho_da_pagina=10" in url
