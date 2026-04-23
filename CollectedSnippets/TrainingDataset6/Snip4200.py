def test_security_scopes_sub_dependency_caching(
    client: TestClient, call_counts: dict[str, int]
):
    response = client.get("/")

    assert response.status_code == 200
    assert call_counts["get_db_session"] == 1
    assert call_counts["get_current_user"] == 2
    assert call_counts["get_user_me"] == 2
    assert call_counts["get_user_items"] == 1
    assert response.json() == {
        "user_me": {
            "user_me": "user_me_1",
            "current_user": {
                "user": "user_1",
                "scopes": ["me"],
                "db_session": "db_session_1",
            },
        },
        "user_items": {
            "user_items": "user_items_1",
            "user_me": {
                "user_me": "user_me_2",
                "current_user": {
                    "user": "user_2",
                    "scopes": ["items", "me"],
                    "db_session": "db_session_1",
                },
            },
        },
    }