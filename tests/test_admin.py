"""Automated checks for Module 2 (Admin Listing Verification)."""
import pytest

import db
from app import create_app


@pytest.fixture()
def client(tmp_path):
    app = create_app(db_path=str(tmp_path / "test.db"))
    app.config["TESTING"] = True
    return app.test_client(), app


def add_listing(app, category="Plastic"):
    return db.add_listing(app.config["DB_PATH"], category, 5, "Good", "Sorted items", 100.0)


def status_of(app, listing_id):
    return db.get_listing(app.config["DB_PATH"], listing_id)["status"]


def test_admin_page_empty_message(client):
    c, _ = client
    assert b"No listings submitted" in c.get("/admin/listings").data


def test_admin_sees_submitted_listing_with_details(client):
    c, app = client
    add_listing(app)
    r = c.get("/admin/listings")
    assert b"Plastic" in r.data and b"Sorted items" in r.data and b"Pending" in r.data


def test_pending_listed_before_decided(client):
    c, app = client
    first = add_listing(app, "Metal")
    add_listing(app, "Glass")
    c.post(f"/admin/listings/{first}/decision", data={"decision": "approve"})
    body = c.get("/admin/listings").data.decode()
    assert body.index("Glass") < body.index("Metal")  # Glass (Pending) first


def test_approve_without_reason(client):
    c, app = client
    lid = add_listing(app)
    r = c.post(f"/admin/listings/{lid}/decision", data={"decision": "approve"})
    assert r.status_code == 302
    assert status_of(app, lid) == "Approved"


@pytest.mark.parametrize(
    "action,expected",
    [("reject", "Rejected"), ("return", "Needs Correction")],
)
def test_reject_and_return_save_reason(client, action, expected):
    c, app = client
    lid = add_listing(app)
    r = c.post(f"/admin/listings/{lid}/decision", data={"decision": action, "reason": "Photo missing"})
    assert r.status_code == 302
    assert status_of(app, lid) == expected
    d = db.get_decisions(app.config["DB_PATH"], lid)
    assert d[0]["reason"] == "Photo missing" and d[0]["decision"] == expected and d[0]["decided_at"]


@pytest.mark.parametrize("action", ["reject", "return"])
def test_reason_mandatory_for_reject_and_return(client, action):
    c, app = client
    lid = add_listing(app)
    r = c.post(f"/admin/listings/{lid}/decision", data={"decision": action, "reason": "   "})
    assert r.status_code == 400
    assert b"reason is required" in r.data
    assert status_of(app, lid) == "Pending"
    assert db.get_decisions(app.config["DB_PATH"], lid) == []


def test_no_decision_selected_is_rejected(client):
    c, app = client
    lid = add_listing(app)
    r = c.post(f"/admin/listings/{lid}/decision", data={"decision": ""})
    assert r.status_code == 400
    assert status_of(app, lid) == "Pending"


def test_reason_too_long_rejected(client):
    c, app = client
    lid = add_listing(app)
    r = c.post(f"/admin/listings/{lid}/decision", data={"decision": "reject", "reason": "x" * 301})
    assert r.status_code == 400
    assert status_of(app, lid) == "Pending"


def test_cannot_decide_twice(client):
    c, app = client
    lid = add_listing(app)
    c.post(f"/admin/listings/{lid}/decision", data={"decision": "approve"})
    r = c.post(f"/admin/listings/{lid}/decision", data={"decision": "reject", "reason": "late"})
    assert r.status_code == 400
    assert status_of(app, lid) == "Approved"


def test_unknown_listing_404(client):
    c, _ = client
    assert c.get("/admin/listings/999").status_code == 404
    assert c.post("/admin/listings/999/decision", data={"decision": "approve"}).status_code == 404


def test_marketplace_empty_message(client):
    c, _ = client
    assert b"No approved listings yet" in c.get("/marketplace").data


def test_marketplace_shows_only_approved(client):
    c, app = client
    approved = add_listing(app, "Metal")
    rejected = add_listing(app, "Glass")
    returned = add_listing(app, "Paper")
    add_listing(app, "E-waste")  # stays Pending
    c.post(f"/admin/listings/{approved}/decision", data={"decision": "approve"})
    c.post(f"/admin/listings/{rejected}/decision", data={"decision": "reject", "reason": "x"})
    c.post(f"/admin/listings/{returned}/decision", data={"decision": "return", "reason": "x"})
    body = c.get("/marketplace").data
    assert b"Metal" in body
    for hidden in (b"Glass", b"Paper", b"E-waste"):
        assert hidden not in body


def test_listing_appears_immediately_after_approval(client):
    c, app = client
    lid = add_listing(app, "Metal")
    assert b"Metal" not in c.get("/marketplace").data
    c.post(f"/admin/listings/{lid}/decision", data={"decision": "approve"})
    assert b"Metal" in c.get("/marketplace").data
