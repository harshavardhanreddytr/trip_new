import pytest
import os


@pytest.mark.skip(reason="CSV import route under refactor; tested later")
def test_csv_import_success(client):
    csv_path = os.path.join("tests", "fixtures", "good_trip.csv")

    with open(csv_path, "rb") as f:
        response = client.post(
            "/import_csv",
            data={"file": f},
            content_type="multipart/form-data",
        )

    assert response.status_code in (200, 302)