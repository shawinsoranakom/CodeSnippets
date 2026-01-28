def test_get_user_history_empty_results(
    mocker: pytest_mock.MockerFixture,
    snapshot: Snapshot,
) -> None:
    """Test user credit history with no results"""
    # Mock empty history response
    mock_history_response = UserHistoryResponse(
        history=[],
        pagination=Pagination(
            total_items=0,
            total_pages=0,
            current_page=1,
            page_size=20,
        ),
    )

    mocker.patch(
        "backend.api.features.admin.credit_admin_routes.admin_get_user_history",
        return_value=mock_history_response,
    )

    response = client.get("/admin/users_history", params={"search": "nonexistent"})

    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data["history"]) == 0
    assert response_data["pagination"]["total_items"] == 0

    # Snapshot test the response
    snapshot.snapshot_dir = "snapshots"
    snapshot.assert_match(
        json.dumps(response_data, indent=2, sort_keys=True),
        "adm_usr_hist_empty",
    )


def test_add_credits_invalid_request() -> None:
    """Test credit addition with invalid request data"""
    # Missing required fields
    response = client.post("/admin/add_credits", json={})
    assert response.status_code == 422

    # Invalid amount type
    response = client.post(
        "/admin/add_credits",
        json={
            "user_id": "test",
            "amount": "not_a_number",
            "comments": "test",
        },
    )
    assert response.status_code == 422

    # Missing comments
    response = client.post(
        "/admin/add_credits",
        json={
            "user_id": "test",
            "amount": 100,
        },
    )
    assert response.status_code == 422
