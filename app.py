"""Digital Recycling Marketplace - Flask app.

Module 1: Recycling Item Listing Management
Module 2: Admin Listing Verification
Integration: seller -> admin decision -> marketplace, with correction loop.
"""
import os

from flask import Flask, abort, flash, redirect, render_template, request, url_for

import db
from validation import (
    CATEGORIES,
    CONDITIONS,
    MAX_DESCRIPTION,
    MAX_REASON,
    validate_decision,
    validate_listing,
)


def create_app(db_path=None):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")
    app.config["DB_PATH"] = db_path or os.path.join(app.root_path, "marketplace.db")
    db.init_db(app.config["DB_PATH"])

    def form_context(**extra):
        ctx = dict(
            categories=CATEGORIES,
            conditions=CONDITIONS,
            max_description=MAX_DESCRIPTION,
            form={},
            errors={},
        )
        ctx.update(extra)
        return ctx

    @app.route("/")
    def home():
        counts = db.get_status_counts(app.config["DB_PATH"])
        return render_template("home.html", counts=counts, total=sum(counts.values()))

    # ---------------- Module 1: Listing Management ----------------

    @app.route("/listings/new", methods=["GET", "POST"])
    def new_listing():
        form_data, errors = {}, {}
        if request.method == "POST":
            form_data = request.form
            clean, errors = validate_listing(request.form)
            if not errors:
                db.add_listing(
                    app.config["DB_PATH"],
                    clean["category"],
                    clean["quantity"],
                    clean["condition"],
                    clean["description"],
                    clean["price"],
                )
                flash("Listing submitted successfully. Status: Pending.", "success")
                return redirect(url_for("my_listings"))
        return render_template("listing_form.html", **form_context(form=form_data, errors=errors))

    @app.route("/listings")
    def my_listings():
        listings = db.get_all_listings(app.config["DB_PATH"])
        return render_template("listings.html", listings=listings)

    @app.route("/listings/<int:listing_id>/edit", methods=["GET", "POST"])
    def edit_listing(listing_id):
        """Seller corrects a listing the admin returned (integration, DRM-8)."""
        listing = db.get_listing(app.config["DB_PATH"], listing_id)
        if listing is None:
            abort(404)
        if listing["status"] != "Needs Correction":
            flash("Only listings marked 'Needs Correction' can be edited.", "error")
            return redirect(url_for("my_listings"))

        note = db.get_latest_reason(app.config["DB_PATH"], listing_id)
        form_data, errors = dict(listing), {}
        if request.method == "POST":
            form_data = request.form
            clean, errors = validate_listing(request.form)
            if not errors:
                db.resubmit_listing(
                    app.config["DB_PATH"], listing_id, clean["category"], clean["quantity"],
                    clean["condition"], clean["description"], clean["price"],
                )
                flash(f"Listing #{listing_id} corrected and resubmitted. Status: Pending.", "success")
                return redirect(url_for("my_listings"))
        return render_template(
            "listing_form.html",
            **form_context(
                form=form_data, errors=errors, note=note,
                heading=f"Correct Listing #{listing_id}", submit_label="Resubmit Listing",
            ),
        )

    # ---------------- Module 2: Admin Listing Verification ----------------

    @app.route("/admin/listings")
    def admin_listings():
        status = request.args.get("status")
        if status not in db.STATUSES:
            status = None
        listings = db.get_listings_for_admin(app.config["DB_PATH"], status)
        return render_template(
            "admin_listings.html", listings=listings, statuses=db.STATUSES, active_status=status
        )

    @app.route("/admin/listings/<int:listing_id>")
    def admin_review(listing_id):
        listing = db.get_listing(app.config["DB_PATH"], listing_id)
        if listing is None:
            abort(404)
        decisions = db.get_decisions(app.config["DB_PATH"], listing_id)
        return render_template(
            "admin_review.html", listing=listing, decisions=decisions,
            max_reason=MAX_REASON, error=None, reason="",
        )

    @app.route("/admin/listings/<int:listing_id>/decision", methods=["POST"])
    def admin_decide(listing_id):
        listing = db.get_listing(app.config["DB_PATH"], listing_id)
        if listing is None:
            abort(404)
        new_status, reason, error = validate_decision(request.form)
        if error is None and not db.record_decision(
            app.config["DB_PATH"], listing_id, new_status, reason
        ):
            error = "This listing has already been decided."
        if error:
            decisions = db.get_decisions(app.config["DB_PATH"], listing_id)
            return render_template(
                "admin_review.html", listing=listing, decisions=decisions,
                max_reason=MAX_REASON, error=error, reason=reason,
            ), 400
        flash(f"Listing #{listing_id} marked as {new_status}.", "success")
        return redirect(url_for("admin_listings"))

    @app.route("/marketplace")
    def marketplace():
        listings = db.get_approved_listings(app.config["DB_PATH"])
        return render_template("marketplace.html", listings=listings)

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("404.html"), 404

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
