"""Digital Recycling Marketplace - Flask app.

Module 1: Recycling Item Listing Management
(Module 2, Admin Listing Verification, is added on Day 3.)
"""
import os

from flask import Flask, flash, redirect, render_template, request, url_for

import db
from validation import CATEGORIES, CONDITIONS, MAX_DESCRIPTION, validate_listing


def create_app(db_path=None):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")
    app.config["DB_PATH"] = db_path or os.path.join(app.root_path, "marketplace.db")
    db.init_db(app.config["DB_PATH"])

    @app.route("/")
    def home():
        return redirect(url_for("my_listings"))

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
        return render_template(
            "listing_form.html",
            categories=CATEGORIES,
            conditions=CONDITIONS,
            max_description=MAX_DESCRIPTION,
            form=form_data,
            errors=errors,
        )

    @app.route("/listings")
    def my_listings():
        listings = db.get_all_listings(app.config["DB_PATH"])
        return render_template("listings.html", listings=listings)

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
