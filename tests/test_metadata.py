"""Resource and filter metadata, and filter validation."""

from __future__ import annotations

import datetime as dt
import math

import pytest

import obrasgovpy as og
from obrasgovpy import metadata
from obrasgovpy._errors import FilterError
from tests.conftest import add_page, page_body


def test_resources_are_discoverable():
    resources = og.list_resources()

    assert len(resources) == 8
    assert "get_projects" in set(resources["function"])
    assert resources.loc[resources["resource"] == "last_update", "paginated"].item() is False


def test_filters_are_discoverable():
    filters = og.list_filters("geometries")

    assert "sg_uf" in set(filters["filter"])
    assert filters.loc[filters["filter"] == "cod_ibge", "type"].item() == "int"


def test_portuguese_resource_names_are_accepted():
    assert len(og.list_filters("geometrias")) == len(og.list_filters("geometries"))


def test_unknown_resources_are_rejected():
    with pytest.raises(ValueError, match="Unknown resource"):
        og.list_filters("missing")


def test_enum_filters_expose_the_values_the_openapi_contract_declares():
    def allowed(resource, name):
        filters = og.list_filters(resource)
        return filters.loc[filters["filter"] == name, "allowed_values"].item()

    assert "Obra" in allowed("projects", "natureza_intervencao")
    assert "Construção" in allowed("projects", "especie_intervencao")
    assert "Em execução" in allowed("projects", "situacao")
    assert "Serviços de Engenharia" in allowed("contracts", "categoria_contrato")
    assert "Par de Lat/Long" in allowed("geometries", "origem_geometria")
    assert "Técnica" in allowed("feasibility_studies", "tipo_estudo_viabilidade")


def test_every_filter_matches_the_r_sibling_counts():
    # The two packages freeze the same OpenAPI contract and must agree.
    counts = {
        "projects": 29,
        "commitments": 28,
        "physical_execution": 9,
        "contracts": 22,
        "geometries": 6,
        "status_history": 7,
        "feasibility_studies": 3,
        "last_update": 0,
    }
    for resource, expected in counts.items():
        assert len(metadata.RESOURCES[resource]["filters"]) == expected, resource


def test_unknown_filters_are_rejected_before_any_request():
    with pytest.raises(FilterError, match="uf_principal_typo"):
        og.get_projects(uf_principal_typo="PE")


def test_none_filters_are_dropped(mock):
    add_page(mock, page_body(1))

    og.get_projects(uf_principal="PE", situacao=None)

    url = mock.calls[0].request.url
    assert "uf_principal=PE" in url
    assert "situacao" not in url


def test_list_filters_values_are_rejected():
    with pytest.raises(FilterError, match="one value"):
        og.get_projects(uf_principal=["PE", "BA"])


def test_nan_filter_values_are_rejected():
    with pytest.raises(FilterError, match="non-missing"):
        og.get_projects(populacao_beneficiada=math.nan)


def test_date_filters_are_serialized_in_iso_format(mock):
    add_page(mock, page_body(1))

    og.get_projects(dt_cadastro=dt.date(2025, 1, 31))

    assert "dt_cadastro=2025-01-31" in mock.calls[0].request.url
