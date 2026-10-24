"""Automated checks for Module 1 (Listing Management)."""
import pytest

import db
from app import create_app


@pytest.fixture()
def client(tmp_path):
    app = create_app(db_path=str(tmp_path / "test.db"))
    app.config["TESTING"] = True
    return app.test_client(), app


def valid_form(**overrides):
    data = {
        "category": "Plastic",
        "quantity": "10",
        "condition": "Good",
        "description": "Clean PET bottles, sorted.",
        "price": "250.50",
    }
    data.update(overrides)
    return data


def count_rows(app):
    return len(db.get_all_listings(app.config["DB_PATH"]))


def test_form_page_loads(client):
    c, _ = client
    r = c.get("/listings/new")
    assert r.status_code == 200
    for field in (b"category", b"quantity", b"condition", b"description", b"price"):
        assert field in r.data


def test_valid_listing_saved_as_pending(client):
    c, app = client
    r = c.post("/listings/new", data=valid_form(), follow_redirects=True)
    assert r.status_code == 200
    assert b"submitted successfully" in r.data
    rows = db.get_all_listings(app.config["DB_PATH"])
    assert len(rows) == 1
    assert rows[0]["status"] == "Pending"
    assert rows[0]["price"] == 250.5


@pytest.mark.parametrize(
    "overrides",
    [
        {"category": ""},
        {"quantity": "0"},
        {"quantity": "-3"},
        {"quantity": "abc"},
        {"quantity": "2.5"},
        {"condition": ""},
        {"description": ""},
        {"description": "x" * 501},
        {"price": "0"},
        {"price": "-1"},
        {"price": "abc"},
    ],
)
def test_invalid_input_not_saved(client, overrides):
    c, app = client
    r = c.post("/listings/new", data=valid_form(**overrides))
    assert r.status_code == 200
    assert b'class="error"' in r.data
    assert count_rows(app) == 0


def test_boundary_values_accepted(client):
    c, app = client
    c.post("/listings/new", data=valid_form(quantity="1", price="0.01", description="x" * 500))
    assert count_rows(app) == 1


def test_empty_listings_page_message(client):
    c, _ = client
    r = c.get("/listings")
    assert b"No listings yet" in r.data


def test_listings_page_shows_status(client):
    c, _ = client
    c.post("/listings/new", data=valid_form())
    r = c.get("/listings")
    assert b"Plastic" in r.data
    assert b"Pending" in r.data
