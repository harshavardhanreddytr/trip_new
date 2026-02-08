def test_sanity():
    assert True


def test_app_starts(client):
    response = client.get("/")
    assert response.status_code in [200, 302]