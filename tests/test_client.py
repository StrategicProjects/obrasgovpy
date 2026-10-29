"""Transport behavior: user agent, errors, retries and the envelope checks."""

from __future__ import annotations

import pytest

import obrasgovpy as og
from obrasgovpy import _client
from obrasgovpy._errors import HTTPError, ResponseError
from tests.conftest import BASE, add_page, page_body


def test_user_agent_reports_the_package_version():
    agent = _client._user_agent()
    assert agent.startswith(f"obrasgovpy/{og.__version__} ")


def test_requests_carry_accept_and_user_agent(mock):
    add_page(mock, page_body(1))
    og.get_projects(page_size=50)

    sent = mock.calls[0].request
    assert sent.headers["Accept"] == "application/json"
    assert sent.headers["User-Agent"].startswith("obrasgovpy/")


def test_only_https_base_urls_are_accepted():
    with pytest.raises(ValueError, match="HTTPS"):
        og.get_projects(base_url="http://example.test/obras")


def test_unknown_configure_option_is_rejected():
    with pytest.raises(ValueError, match="Unknown option"):
        og.configure(verify_tls=False)


def test_http_errors_carry_status_and_detail(mock):
    mock.get(
        f"{BASE}/projeto-investimento",
        body='{"detail":"Too many requests"}',
        status=429,
        content_type="application/json",
    )

    with pytest.raises(HTTPError) as caught:
        og.get_projects()

    assert caught.value.status == 429
    assert "429" in str(caught.value)
    assert "Too many requests" in str(caught.value)


def test_validation_errors_name_the_offending_parameter(mock):
    body = (
        '{"detail":[{"loc":["query","ano_cadastro"],'
        '"msg":"value is not a valid integer","type":"type_error"}]}'
    )
    mock.get(
        f"{BASE}/projeto-investimento", body=body, status=422,
        content_type="application/json",
    )

    with pytest.raises(HTTPError, match="ano_cadastro"):
        og.get_projects()


def test_a_non_object_error_body_does_not_mask_the_status(mock):
    mock.get(
        f"{BASE}/projeto-investimento", body='"gateway timeout"', status=504,
        content_type="application/json",
    )

    with pytest.raises(HTTPError) as caught:
        og.get_projects()
    assert caught.value.status == 504


def test_invalid_json_is_a_response_error(mock):
    mock.get(
        f"{BASE}/projeto-investimento", body="<html>maintenance</html>",
        status=200, content_type="text/html",
    )

    with pytest.raises(ResponseError, match="not valid JSON"):
        og.get_projects()


def test_transient_statuses_are_retried(mock):
    og.configure(max_tries=2)
    mock.get(f"{BASE}/projeto-investimento", body="busy", status=503)
    add_page(mock, page_body(1))

    frame = og.get_projects()

    assert len(frame) == 1
    assert len(mock.calls) == 2


def test_a_422_is_not_retried(mock):
    og.configure(max_tries=3)
    mock.get(
        f"{BASE}/projeto-investimento", body='{"detail":"bad"}', status=422,
        content_type="application/json",
    )

    with pytest.raises(HTTPError):
        og.get_projects()
    assert len(mock.calls) == 1


def test_an_envelope_without_data_is_rejected(mock):
    add_page(mock, '{"total_pages":1,"total_items":1,"page_number":1,"page_size":50}')

    with pytest.raises(ResponseError, match="unexpected format"):
        og.get_projects()


def test_data_must_be_an_array(mock):
    add_page(
        mock,
        '{"data":{"id":1},"total_pages":1,"total_items":1,'
        '"page_number":1,"page_size":50}',
    )

    with pytest.raises(ResponseError, match="unexpected format"):
        og.get_projects()
