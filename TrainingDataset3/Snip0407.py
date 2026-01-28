def test_get_user_history_with_filters(
    mocker: pytest_mock.MockerFixture,
    snapshot: Snapshot,
) -> None:
    """Test user credit history with search and filter parameters"""
    # Mock the admin_get_user_history function
    mock_history_response = UserHistoryResponse(
        history=[
            UserTransaction(
                user_id="user-3",
                user_email="test@example.com",
                amount=500,
                reason="Top up",
                transaction_type=prisma.enums.CreditTransactionType.TOP_UP,
            ),
        ],
        pagination=Pagination(
            total_items=1,
            total_pages=1,
            current_page=1,
            page_size=10,
        ),
    )

    mock_get_history = mocker.patch(
        "backend.api.features.admin.credit_admin_routes.admin_get_user_history",
        return_value=mock_history_response,
    )

    response = client.get(
        "/admin/users_history",
        params={
            "search": "test@example.com",
            "page": 1,
            "page_size": 10,
            "transaction_filter": "TOP_UP",
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data["history"]) == 1
    assert response_data["history"][0]["transaction_type"] == "TOP_UP"

    # Verify the function was called with correct parameters
    mock_get_history.assert_called_once_with(
        page=1,
        page_size=10,
        search="test@example.com",
        transaction_filter=prisma.enums.CreditTransactionType.TOP_UP,
    )

    # Snapshot test the response
    snapshot.snapshot_dir = "snapshots"
    snapshot.assert_match(
        json.dumps(response_data, indent=2, sort_keys=True),
        "adm_usr_hist_filt",
    )
