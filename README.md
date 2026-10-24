# Digital Recycling Marketplace (PBL)

Individual PBL project managed in Jira (project key: DRM).

## Modules
1. Recycling Item Listing Management (Day 2 - implemented)
2. Admin Listing Verification (Day 3 - pending)

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

## Tests
```
python -m pytest -q
```
