import pytest
import requests
from unittest.mock import patch, MagicMock
from task_Vyazmin_Ilja_asset_web_service import app, Asset, ANSWER_PAGE_NOT_FOUND
from flask import jsonify


TEST_BANK = [
	("AMD/name/1000/0.5", ("This name already exist", 403)),
	("RUB/name2/20000/1", ("Asset name2 was successfully added", 200)),
	("USD/name1/1000/0.5", ("Asset name1 was successfully added", 200)),
]

TEST_BANK_RESPONSE = [
	["AMD", "name", 1000.0, 0.5],
	["RUB", "name2", 20000.0, 1.0],
	["USD", "name1", 1000.0, 0.5]
]


@pytest.fixture
def client():
	with app.test_client() as client:
		yield client


def test_page_not_found(client):
	app_response = client.get("/search")
	assert app_response.status_code == 404
	assert app_response.data.decode(app_response.charset) == ANSWER_PAGE_NOT_FOUND


# @patch("requests.get")
# def test_cbr_not_avalible(mock_requests_get, client):
# 	mock_requests_get.status_code.value = 500
# 	response = client.get("/cbr/daily")
# 	assert response.status_code == 503
# 	assert response.text == "CBR service is unavailable"


# def callback_requests_get(url):
# 	app_response = requests.get("/cbr/daily/xxx")
# 	return app_response


def test_cbr_daily(client):
	app_response = client.get("/cbr/daily", follow_redirects=True)
	assert app_response.status_code == 200

	assert app_response.is_json
	json_response = app_response.get_json()
	assert 6 < json_response["TJS"] < 7


def test_cbr_key_indicators(client):
	app_response = client.get("/cbr/key_indicators", follow_redirects=True)
	assert app_response.status_code == 200
	assert app_response.is_json
	json_response = app_response.get_json()
	assert json_response["Pd"] > 5000
	assert len(json_response) == 6


@pytest.mark.parametrize(
	"asset_url, answer", TEST_BANK)
def test_can_add_asset(client, asset_url, answer):
	app.bank = {'name': Asset('name', 'USD', 100, 0.5)}
	app_response = client.get("/api/asset/add/" + asset_url)
	
	assert app_response.status_code == answer[1]


def test_can_get_assets_list(client):
	app.bank = dict()
	for asset in TEST_BANK:
		app_response = client.get("/api/asset/add/" + asset[0])
	app_response = client.get("/api/asset/list")
	assert app_response.status_code == 200
	assert app_response.data.decode(app_response.charset) == jsonify(TEST_BANK_RESPONSE).data.decode(app_response.charset)

def test_can_clean_bank(client):
	for asset in TEST_BANK:
		app_response = client.get("/api/asset/add/" + asset[0])
	app_response = client.get("/api/asset/cleanup")
	assert app_response.status_code == 200
	assert len(app.bank) == 0

def test_can_get_some_assets(client):
	app.bank = dict()
	for asset in TEST_BANK:
		app_response = client.get("/api/asset/add/" + asset[0])
	app_response = client.get("/api/asset/get?name=name1&name=name2")
	assert app_response.status_code == 200
	assert app_response.data.decode(app_response.charset) == jsonify(TEST_BANK_RESPONSE[1:]).data.decode(app_response.charset)


# def test_can_calculate_revenue(client):
# 	