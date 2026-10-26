# Digital Recycling Marketplace (PBL)

Individual PBL project managed in Jira (project key: DRM).

## Modules
1. Recycling Item Listing Management
2. Admin Listing Verification

## Tech stack
Python 3, Flask, SQLite, HTML/CSS

## Run locally
```
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

## Pages (Module 1)
- `/listings/new` - create a listing (category, quantity, condition, description, price)
- `/listings` - view listings with status

## Pages (Module 2)
- `/admin/listings` - admin: all submitted listings (Pending first)
- `/admin/listings/<id>` - admin: review, Approve / Reject / Return for Correction with reason
- `/marketplace` - public marketplace, approved listings only

## Integration
- `/` - home dashboard with listing counts per status
- `/listings/<id>/edit` - seller corrects a listing returned by the admin; it goes back to Pending
- Seller's `/listings` page shows the admin's reason for Rejected / Needs Correction
- `/admin/listings?status=Pending` - admin filter by status

## Tests
```
python -m pytest -q
```
