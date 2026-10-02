SAMPLE_CSV = """episode_id,robot_id,task_name,recorded_at,duration_seconds,operator_name,quality
EP-A001,arm-01,pick cup,2026-08-01T10:00:00,30,Alice,good
EP-A001,arm-01,pick cup,2026-08-01T10:00:00,30,Alice,good
,mobile-01,fold towel,2026-08-02T10:00:00,40,Bob,good
EP-A002,arm-99,pick cup,2026-08-03T10:00:00,30,Alice,good
EP-A003,arm-01,pick cup,not-a-date,30,Alice,good
EP-A004,arm-01,pick cup,2026-08-04T10:00:00,N/A,Alice,good
EP-A005,arm-01,pick cup,2026-08-05T10:00:00,30,,usable
EP-A006,arm-01,pick cup,2026-08-06T10:00:00,30,Alice,excellent
"""


def test_import_via_api(client, operator_token):
    resp1 = client.post(
        "/api/episodes/import",
        files={"file": ("test.csv", SAMPLE_CSV, "text/csv")},
        headers={"Authorization": f"Bearer {operator_token}"},
    )
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["imported"] == 2
    assert data1["skipped"] >= 5

    resp2 = client.post(
        "/api/episodes/import",
        files={"file": ("test.csv", SAMPLE_CSV, "text/csv")},
        headers={"Authorization": f"Bearer {operator_token}"},
    )
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["imported"] == 0
