"""Input validation for the listing form (DRM-13)."""

CATEGORIES = ("Plastic", "Paper", "Metal", "Glass", "E-waste", "Other")
CONDITIONS = ("New", "Like New", "Good", "Fair", "Poor")

MAX_QUANTITY = 10000
MAX_PRICE = 1000000
MAX_DESCRIPTION = 500


def validate_listing(form):
    """Validate raw form data.

    Returns (clean, errors). `clean` holds converted values,
    `errors` maps field name -> error message. Nothing should be saved
    when `errors` is not empty.
    """
    errors = {}
    clean = {}

    category = (form.get("category") or "").strip()
    if not category:
        errors["category"] = "Category is required."
    elif category not in CATEGORIES:
        errors["category"] = "Please choose a valid category."
    else:
        clean["category"] = category

    quantity_raw = (form.get("quantity") or "").strip()
    if not quantity_raw:
        errors["quantity"] = "Quantity is required."
    else:
        try:
            quantity = int(quantity_raw)
        except ValueError:
            errors["quantity"] = "Quantity must be a whole number."
        else:
            if quantity <= 0:
                errors["quantity"] = "Quantity must be greater than 0."
            elif quantity > MAX_QUANTITY:
                errors["quantity"] = f"Quantity cannot exceed {MAX_QUANTITY}."
            else:
                clean["quantity"] = quantity

    condition = (form.get("condition") or "").strip()
    if not condition:
        errors["condition"] = "Condition is required."
    elif condition not in CONDITIONS:
        errors["condition"] = "Please choose a valid condition."
    else:
        clean["condition"] = condition

    description = (form.get("description") or "").strip()
    if not description:
        errors["description"] = "Description is required."
    elif len(description) > MAX_DESCRIPTION:
        errors["description"] = f"Description cannot exceed {MAX_DESCRIPTION} characters."
    else:
        clean["description"] = description

    price_raw = (form.get("price") or "").strip()
    if not price_raw:
        errors["price"] = "Price is required."
    else:
        try:
            price = float(price_raw)
        except ValueError:
            errors["price"] = "Price must be a number."
        else:
            if price != price or price in (float("inf"), float("-inf")):
                errors["price"] = "Price must be a valid number."
            elif price <= 0:
                errors["price"] = "Price must be greater than 0."
            elif price > MAX_PRICE:
                errors["price"] = f"Price cannot exceed {MAX_PRICE}."
            else:
                clean["price"] = round(price, 2)

    return clean, errors


# ---------------- Admin decision validation (DRM-15/16) ----------------

DECISIONS = {
    "approve": "Approved",
    "reject": "Rejected",
    "return": "Needs Correction",
}
REASON_REQUIRED = ("reject", "return")
MAX_REASON = 300


def validate_decision(form):
    """Validate the admin decision form.

    Returns (new_status, reason, error). `error` is None when valid.
    A reason is mandatory for Reject and Return for Correction.
    """
    action = (form.get("decision") or "").strip()
    reason = (form.get("reason") or "").strip()

    if action not in DECISIONS:
        return None, reason, "Please choose Approve, Reject or Return for Correction."
    if action in REASON_REQUIRED and not reason:
        return None, reason, "A reason is required for Reject and Return for Correction."
    if len(reason) > MAX_REASON:
        return None, reason, f"Reason cannot exceed {MAX_REASON} characters."
    return DECISIONS[action], reason, None
