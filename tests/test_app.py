import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

def test_get_activities():
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    # Check that we have some activities
    assert len(data) > 0
    # Check structure of an activity
    activity = next(iter(data.values()))
    assert "description" in activity
    assert "schedule" in activity
    assert "max_participants" in activity
    assert "participants" in activity

def test_root_redirect():
    response = client.get("/")
    assert response.status_code == 200
    # Should redirect to static/index.html, but TestClient follows redirects
    # Actually, since it's a redirect, it should follow to the static file
    # But since static files are mounted, it might not work in test
    # Let's check what happens
    assert "text/html" in response.headers.get("content-type", "")

def test_signup_success():
    # First get activities to find one with space for signup
    response = client.get("/activities")
    activities = response.json()
    
    # Find an activity with available spots
    activity_name = None
    for name, details in activities.items():
        if len(details["participants"]) < details["max_participants"]:
            activity_name = name
            break
    
    if activity_name:
        email = "test@example.com"
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        
        # Check that the participant was added
        response = client.get("/activities")
        activities = response.json()
        assert email in activities[activity_name]["participants"]

def test_signup_already_signed_up():
    # First signup
    response = client.get("/activities")
    activities = response.json()
    activity_name = next(iter(activities.keys()))
    email = "duplicate@example.com"
    
    # First signup
    client.post(f"/activities/{activity_name}/signup?email={email}")
    
    # Try to signup again
    response = client.post(f"/activities/{activity_name}/signup?email={email}")
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data

def test_signup_activity_not_found():
    response = client.post("/activities/NonExistentActivity/signup?email=test@example.com")
    assert response.status_code == 404

def test_unregister_success():
    # First signup
    response = client.get("/activities")
    activities = response.json()
    activity_name = next(iter(activities.keys()))
    email = "unregister@example.com"
    
    client.post(f"/activities/{activity_name}/signup?email={email}")
    
    # Now unregister
    response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    
    # Check that the participant was removed
    response = client.get("/activities")
    activities = response.json()
    assert email not in activities[activity_name]["participants"]

def test_unregister_not_signed_up():
    response = client.get("/activities")
    activities = response.json()
    activity_name = next(iter(activities.keys()))
    email = "notsignedup@example.com"
    
    response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
    assert response.status_code == 400

def test_unregister_activity_not_found():
    response = client.delete("/activities/NonExistentActivity/unregister?email=test@example.com")
    assert response.status_code == 404