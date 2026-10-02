def _create_request(client, token):
    return client.post(
        "/api/requests",
        json={
            "task_name": "pick cup",
            "episodes_requested": 1,
            "deadline": "2026-12-31T23:59:59Z",
        },
        headers={"Authorization": f"Bearer {token}"},
    )


def test_cannot_assign_bad_episode(client, client_token, operator_token):
    create = _create_request(client, client_token)
    req_id = create.json()["id"]
    episodes = client.get("/api/episodes", headers={"Authorization": f"Bearer {operator_token}"}).json()
    bad_id = next(e["id"] for e in episodes if e["quality"] == "bad")
    resp = client.post(
        f"/api/requests/{req_id}/assign",
        json={"episode_ids": [bad_id]},
        headers={"Authorization": f"Bearer {operator_token}"},
    )
    assert resp.status_code == 400


def test_episode_cannot_be_assigned_twice(client, client_token, operator_token):
    create1 = _create_request(client, client_token)
    create2 = _create_request(client, client_token)
    req1 = create1.json()["id"]
    req2 = create2.json()["id"]

    episodes = client.get("/api/episodes", headers={"Authorization": f"Bearer {operator_token}"}).json()
    good_id = next(e["id"] for e in episodes if e["quality"] == "good")

    resp1 = client.post(
        f"/api/requests/{req1}/assign",
        json={"episode_ids": [good_id]},
        headers={"Authorization": f"Bearer {operator_token}"},
    )
    assert resp1.status_code == 200

    resp2 = client.post(
        f"/api/requests/{req2}/assign",
        json={"episode_ids": [good_id]},
        headers={"Authorization": f"Bearer {operator_token}"},
    )
    assert resp2.status_code == 400
