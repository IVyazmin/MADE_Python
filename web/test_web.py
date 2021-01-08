import json
from contextlib import nullcontext as do_not_raise_exception
from getpass import getpass
from unittest.mock import patch, MagicMock
from json import JSONDecodeError

import requests
import pytest
from requests import exceptions

DEFAULT_ENCODING = "utf-8"
DEFAULT_STATUS_CODE = 200
URL_GITHUB_API = "https://api.github.com"
URL_GITHUB_DOCS = "https://docs.github.com"
GITHUB_API_RESPONSE_FILEPATH = "github_api_response.txt"
GITHUB_DOCS_RESPONSE_FILEPATH = "github_docs_response.html"
URL_AUTH_TEST = "https://jigsaw.w3.org/HTTP/Basic/"
URL_UNKNOWN = "http://it-should-not-exist.com"


def build_response_mock_from_content(content, encoding=DEFAULT_ENCODING, status_code=DEFAULT_STATUS_CODE):
	text=content.decode(encoding)
	response = MagicMock(
		content=content,
		encoding=encoding,
		text=text,
		status_code=status_code,
	)
	response.json.side_effect = lambda: json.loads(text)
	return response


@patch("requests.get")
@pytest.mark.parametrize(
	"target_url, expection",
	[
		(URL_GITHUB_API, do_not_raise_exception()),
		pytest.param(URL_GITHUB_DOCS, pytest.raises(JSONDecodeError), id="raise-JSONDecodeError"),
		(URL_UNKNOWN, pytest.raises(exceptions.ConnectionError))
	]
)
def test_we_can_mock_web(mock_requests_get, target_url, expection):
	mock_requests_get.side_effect = callback_requests_get
	
	with expection:
		response = requests.get(target_url)
		assert response.status_code == 200
		assert "github" in response.text
		assert isinstance(response.json(), dict)


def callback_requests_get(url):
	url_mapping = {
		URL_GITHUB_API: GITHUB_API_RESPONSE_FILEPATH,
		URL_GITHUB_DOCS: GITHUB_DOCS_RESPONSE_FILEPATH,
	}
	if url in url_mapping:
		mock_content_filepath = url_mapping[url]
		with open(mock_content_filepath, "rb") as content_fin:
			content = content_fin.read()
		mock_response = build_response_mock_from_content(content=content)
		return mock_response

	raise exceptions.ConnectionError(f"exceeded max trial connection to {url}")


@pytest.mark.parametrize(
	"target_url, expected_outcome",
	[
		(URL_GITHUB_API, True),
		(URL_AUTH_TEST, False)
	]
)
@pytest.mark.integration_test
def test_http_api_request_is_successful(target_url, expected_outcome):
	response = requests.get(target_url)
	assert expected_outcome == bool(response)


@pytest.mark.integration_test
def test_auth_website_require_correct_credentials():
	response = requests.get(URL_AUTH_TEST, auth=("user", "wrong_password"))
	assert 400 <= response.status_code < 500


@pytest.mark.integration_test
@patch("test_web.getpass")
def test_auth_website_accept_correct_credentials(mock_get_pass):
	mock_get_pass.return_value = "guest"
	response = requests.get(URL_AUTH_TEST, auth=("guest", getpass()))
	assert True == bool(response)
