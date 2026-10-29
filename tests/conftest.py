"""Shared fixtures.

Responses are built from literal JSON rather than from a Python dict wherever
nulls matter: a dict round-tripped through ``json.dumps`` can express ``null``,
but writing the JSON out keeps the tests honest about what the API sends.
"""

from __future__ import annotations

import json

import pytest
import responses as responses_lib

import obrasgovpy as og
from obrasgovpy import _client

BASE = "https://api-publica.obrasgov.gestao.gov.br/obras"


@pytest.fixture(autouse=True)
def isolate():
    """Every test starts without throttling or retries."""
    og.configure(base_url=None, requests_per_minute=0, max_tries=1, timeout=5)
    _client._last_request[0] = 0.0
    yield
    og.configure(base_url=None, requests_per_minute=60, max_tries=4, timeout=30)


@pytest.fixture
def mock():
    with responses_lib.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        yield rsps


def envelope(data, total=0, page=1, page_size=50, pages=None):
    """The paginated envelope, around ``data`` given as literal JSON."""
    if pages is None:
        pages = -(-total // max(page_size, 1))
    return (
        f'{{"data":{data},"total_pages":{pages},"total_items":{total},'
        f'"page_number":{page},"page_size":{page_size}}}'
    )


def project_rows(n, start=1):
    """``n`` projeto-investimento records with ids from ``start``."""
    return [
        {
            "id_projeto_investimento": f"{start + i:06d}.26-07",
            "desc_nome": f"Obra {start + i}",
            "situacao": "Em execução",
            "uf_principal": "PE",
            "dt_cadastro": f"2025-01-0{(i % 9) + 1}",
            "dt_final_efetiva": None,
            "executores": [],
            "tomadores": [{"nome": "Prefeitura", "codigo": start + i}],
        }
        for i in range(n)
    ]


def page_body(n, start=1, total=None, page=1, page_size=50, pages=None):
    """One page of projeto-investimento records."""
    return envelope(
        json.dumps(project_rows(n, start)),
        total=n if total is None else total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


def add_page(mock, body, endpoint="projeto-investimento", status=200):
    mock.get(f"{BASE}/{endpoint}", body=body, status=status,
             content_type="application/json")
