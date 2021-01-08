import pytest
from web_hello_world import app as hello_world_app
from web_hello_world import DEFAULT_GREETING_COUNT, MAX_GREATING_COUNT, REALLY_TOO_MANY_GREETING_COUNT


@pytest.fixture
def client():
	with hello_world_app.test_client() as client:
		yield client


def test_service_reply_to_root_path(client):
	response = client.get("/")
	assert "world" in response.data.decode(response.charset)


def test_service_reply_to_username(client):
	username = "Vasya"
	response = client.get(f"/hello/{username}")
	response_text = response.data.decode(response.charset)
	assert username in response_text


def test_service_reply_to_username_default_count(client):
	username = "Vasya"
	response = client.get(f"/hello/{username}", follow_redirects=True)
	response_text = response.data.decode(response.charset)
	name_count = response_text.count(username)
	assert DEFAULT_GREETING_COUNT == name_count


def test_service_reply_to_username_several_times(client):
	username = "Petya"
	greeting_count = 15
	response = client.get(f"/hello/{username}/{greeting_count}")
	response_text = response.data.decode(response.charset)
	name_count = response_text.count(username)
	assert greeting_count == name_count


def test_service_reply_to_escaped_username(client):
	tag = "<br>"
	username = "Petya"
	greeting_count = 15
	response = client.get(f"/hello/{tag}{username}/{greeting_count}")
	response_text = response.data.decode(response.charset)
	name_count = response_text.count(username)
	assert greeting_count == name_count
	assert 0 == response_text.count(tag)


def test_username_with_slash(client):
	username = "Vasya"
	response = client.get(f"/hello/{username}/")
	assert 200 == response.status_code


def test_service_reply_to_username_too_many_times(client):
	username = "Petya"
	greeting_count = MAX_GREATING_COUNT + 1
	response = client.get(f"/hello/{username}/{greeting_count}", follow_redirects=True)
	response_text = response.data.decode(response.charset)
	name_count = response_text.count(username)
	assert DEFAULT_GREETING_COUNT == name_count


def test_service_reply_to_username_really_too_many_times(client):
	username = "Petya"
	greeting_count = REALLY_TOO_MANY_GREETING_COUNT + 1
	response = client.get(f"/hello/{username}/{greeting_count}", follow_redirects=True)
	response_text = response.data.decode(response.charset)
	name_count = response_text.count(username)
	assert 0 == name_count
	assert 404 == response.status_code