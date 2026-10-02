def _create_request(client, token):
    return client.post(
        "/api/requests",
        json={
            "task_name": "pick cup",
            "episodes_requested": 1,
            "deadline": "2026-12-31T23:59:59Z",
            "notes": "test",
        },
        headers={"Authorization": f"Bearer {token}"},
    )


def login(client, email: str, password: str = "pass123") -> str:
    resp = client.post("/api/auth/login", data={"username": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def test_client_creates_request(client, client_token):
    resp = _create_request(client, client_token)
    assert resp.status_code == 201
    assert resp.json()["status"] == "submitted"


def test_client_sees_only_own_requests(client, client_token):
    _create_request(client, client_token)
    client_resp = client.get("/api/requests", headers={"Authorization": f"Bearer {client_token}"})
    assert len(client_resp.json()) >= 1


def test_invalid_status_transition(client, client_token, operator_token):
    create = _create_request(client, client_token)
    req_id = create.json()["id"]
    resp = client.post(
        f"/api/requests/{req_id}/status",
        json={"status": "delivered"},
        headers={"Authorization": f"Bearer {operator_token}"},
    )
    assert resp.status_code == 400


def test_deliver_requires_enough_episodes(client, client_token, operator_token):
    create = _create_request(client, client_token)
    req_id = create.json()["id"]
    client.post(
        f"/api/requests/{req_id}/status",
        json={"status": "in_progress"},
        headers={"Authorization": f"Bearer {operator_token}"},
    )
    resp = client.post(
        f"/api/requests/{req_id}/status",
        json={"status": "delivered"},
        headers={"Authorization": f"Bearer {operator_token}"},
    )
    assert resp.status_code == 400


def test_full_workflow(client, client_token, operator_token):
    create = _create_request(client, client_token)
    req_id = create.json()["id"]

    episodes = client.get("/api/episodes", headers={"Authorization": f"Bearer {operator_token}"}).json()
    good_id = next(e["id"] for e in episodes if e["quality"] == "good")

    client.post(
        f"/api/requests/{req_id}/assign",
        json={"episode_ids": [good_id]},
        headers={"Authorization": f"Bearer {operator_token}"},
    )

    resp = client.post(
        f"/api/requests/{req_id}/status",
        json={"status": "delivered"},
        headers={"Authorization": f"Bearer {operator_token}"},
    )
    assert resp.status_code == 200

    resp = client.post(
        f"/api/requests/{req_id}/status",
        json={"status": "accepted"},
        headers={"Authorization": f"Bearer {client_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "accepted"


def test_client_cannot_accept_other_clients_request(client, operator_token):
    admin_token = login(client, "admin@test.com")
    other_client = client.post(
        "/api/auth/users",
        json={"email": "other@test.com", "password": "pass123", "role": "client", "name": "Other"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert other_client.status_code == 201

    token_a = login(client, "client@test.com")
    token_b = login(client, "other@test.com")

    create = _create_request(client, token_a)
    req_id = create.json()["id"]

    episodes = client.get("/api/episodes", headers={"Authorization": f"Bearer {operator_token}"}).json()
    good_ids = [e["id"] for e in episodes if e["quality"] == "good"][:1]
    client.post(
        f"/api/requests/{req_id}/assign",
        json={"episode_ids": good_ids},
        headers={"Authorization": f"Bearer {operator_token}"},
    )
    client.post(
        f"/api/requests/{req_id}/status",
        json={"status": "delivered"},
        headers={"Authorization": f"Bearer {operator_token}"},
    )

    resp = client.post(
        f"/api/requests/{req_id}/status",
        json={"status": "accepted"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 400
