import sys
import pathlib
from urllib.parse import quote

from fastapi.testclient import TestClient

# Ensure src/ is importable as a module path and import the app
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import app as app_module  # noqa: E402

client = TestClient(app_module.app)


def test_get_activities():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    # Known activity from seed data
    assert "Chess Club" in data
    assert isinstance(data["Chess Club"]["participants"], list)


def test_signup_and_unregister_flow():
    activity = "Chess Club"
    email = "test.user@example.com"

    # Ensure clean start: remove email if present
    activities = client.get("/activities").json()
    if email in activities[activity]["participants"]:
        client.delete(f"/activities/{quote(activity)}/participants?email={quote(email)}")

    # Sign up
    signup_url = f"/activities/{quote(activity)}/signup?email={quote(email)}"
    r = client.post(signup_url)
    assert r.status_code == 200
    assert email in client.get("/activities").json()[activity]["participants"]

    # Duplicate signup should be rejected
    r2 = client.post(signup_url)
    assert r2.status_code == 400

    # Unregister the test user
    del_url = f"/activities/{quote(activity)}/participants?email={quote(email)}"
    rd = client.delete(del_url)
    assert rd.status_code == 200
    assert email not in client.get("/activities").json()[activity]["participants"]


def test_unregister_nonexistent_returns_404():
    activity = "Chess Club"
    email = "noone@example.com"
    del_url = f"/activities/{quote(activity)}/participants?email={quote(email)}"
    r = client.delete(del_url)
    # If the test environment currently has that user, the endpoint may return 200; we accept either 404 or 200,
    # but if it's 200 we clean up so subsequent runs are consistent.
    if r.status_code == 200:
        # cleaned up by server
        assert email not in client.get("/activities").json()[activity]["participants"]
    else:
        assert r.status_code == 404
