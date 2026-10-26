"""Integration checks: seller -> admin -> marketplace, plus correction loop (DRM-8)."""
import pytest

import db
from app import create_app


@pytest.fixture()
def client(tmp_path):
    app = create_app(db_path=str(tmp_path / "test.db"))
    app.config["TESTING"] = True
    return app.test_client(), app


FORM = {
    "category": "Metal",
    "quantity": "4",
    "condition": "Good",
    "description": "Copper pipes",
    "price": "900",
}


def submit(c, **overrides):
    data = dict(FORM)
    data.update(overrides)
    return c.post("/listings/new", data=data, follow_redirects=True)


def decide(c, listing_id, action, reason=""):
    return c.post(f"/admin/listings/{listing_id}/decision", data={"decision": action, "reason": reason})


def test_full_flow_seller_admin_marketplace(client):
    c, app = client
    submit(c)
    assert b"Metal" not in c.get("/marketplace").data        # Pending: not public
    assert b"Pending" in c.get("/admin/listings").data
    decide(c, 1, "approve")
    assert b"Metal" in c.get("/marketplace").data             # Approved: public
    assert b"Approved" in c.get("/listings").data


def test_rejection_reason_visible_to_seller(client):
    c, _ = client
    submit(c)
    decide(c, 1, "reject", "Not recyclable")
    body = c.get("/listings").data
    assert b"Rejected" in body and b"Not recyclable" in body
    assert b"Metal" not in c.get("/marketplace").data


def test_correction_loop_returns_to_pending(client):
    c, app = client
    submit(c)
    decide(c, 1, "return", "Add a clearer description")
    page = c.get("/listings").data
    assert b"Needs Correction" in page and b"Edit &amp; resubmit" in page
    form = c.get("/listings/1/edit")
    assert form.status_code == 200 and b"Add a clearer description" in form.data
    r = c.post("/listings/1/edit", data=dict(FORM, description="Copper pipes, cleaned, 2 m each"))
    assert r.status_code == 302
    listing = db.get_listing(app.config["DB_PATH"], 1)
    assert listing["status"] == "Pending"
    assert listing["description"] == "Copper pipes, cleaned, 2 m each"
    assert len(db.get_decisions(app.config["DB_PATH"], 1)) == 1   # history kept
    assert b"Pending" in c.get("/admin/listings?status=Pending").data


def test_resubmit_validates_input(client):
    c, app = client
    submit(c)
    decide(c, 1, "return", "Fix price")
    r = c.post("/listings/1/edit", data=dict(FORM, price="0"))
    assert r.status_code == 200 and b"greater than 0" in r.data
    assert db.get_listing(app.config["DB_PATH"], 1)["status"] == "Needs Correction"


@pytest.mark.parametrize("action,reason", [("approve", ""), ("reject", "No")])
def test_cannot_edit_decided_listing(client, action, reason):
    c, app = client
    submit(c)
    decide(c, 1, action, reason)
    assert c.get("/listings/1/edit").status_code == 302
    c.post("/listings/1/edit", data=dict(FORM, category="Glass"))
    assert db.get_listing(app.config["DB_PATH"], 1)["category"] == "Metal"


def test_edit_pending_listing_not_allowed(client):
    c, _ = client
    submit(c)
    assert c.get("/listings/1/edit").status_code == 302


def test_home_shows_counts(client):
    c, _ = client
    assert b"No listings yet" in c.get("/").data
    submit(c)
    submit(c, category="Glass")
    decide(c, 1, "approve")
    counts = db.get_status_counts(c.application.config["DB_PATH"])
    assert counts == {"Pending": 1, "Approved": 1, "Rejected": 0, "Needs Correction": 0}
    assert c.get("/").status_code == 200


def test_admin_status_filter(client):
    c, _ = client
    submit(c, category="Metal")
    submit(c, category="Glass")
    decide(c, 1, "approve")
    body = c.get("/admin/listings?status=Approved").data
    assert b"Metal" in body and b"Glass" not in body
    assert b"Glass" in c.get("/admin/listings?status=bogus").data  # bad filter -> all


def test_404_page(client):
    c, _ = client
    r = c.get("/no-such-page")
    assert r.status_code == 404 and b"Page not found" in r.data
    assert c.get("/listings/999/edit").status_code == 404
