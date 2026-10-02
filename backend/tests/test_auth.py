def login(client, email: str, password: str = "pass123") -> str:
    resp = client.post("/api/auth/login", data={"username": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def test_login_success(client):
    resp = client.post("/api/auth/login", data={"username": "client@test.com", "password": "pass123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_failure(client):
    resp = client.post("/api/auth/login", data={"username": "client@test.com", "password": "wrong"})
    assert resp.status_code == 401


def test_client_cannot_list_episodes(client, client_token):
    resp = client.get("/api/episodes", headers={"Authorization": f"Bearer {client_token}"})
    assert resp.status_code == 403


def test_operator_can_list_episodes(client, operator_token):
    resp = client.get("/api/episodes", headers={"Authorization": f"Bearer {operator_token}"})
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_admin_can_create_user(client, admin_token):
    resp = client.post(
        "/api/auth/users",
        json={
            "email": "new@test.com",
            "password": "pass123",
            "role": "client",
            "name": "New User",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201


def test_operator_cannot_create_user(client, operator_token):
    resp = client.post(
        "/api/auth/users",
        json={
            "email": "new2@test.com",
            "password": "pass123",
            "role": "client",
            "name": "New User",
        },
        headers={"Authorization": f"Bearer {operator_token}"},
    )
    assert resp.status_code == 403
