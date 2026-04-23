def test_get_user_history_success(
    mocker: pytest_mock.MockerFixture,
    snapshot: Snapshot,
) -> None:
    """Test successful retrieval of user credit history"""
    # Mock the admin_get_user_history function
    mock_history_response = UserHistoryResponse(
        history=[
            UserTransaction(
                user_id="user-1",
                user_email="user1@example.com",
                amount=1000,
                reason="Initial grant",
                transaction_type=prisma.enums.CreditTransactionType.GRANT,
            ),
            UserTransaction(
                user_id="user-2",
                user_email="user2@example.com",
                amount=-50,
                reason="Usage",
                transaction_type=prisma.enums.CreditTransactionType.USAGE,
            ),
        ],
        pagination=Pagination(
            total_items=2,
            total_pages=1,
            current_page=1,
            page_size=20,
        ),
    )

    mocker.patch(
        "backend.api.features.admin.credit_admin_routes.admin_get_user_history",
        return_value=mock_history_response,
    )

    response = client.get("/admin/users_history")

    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data["history"]) == 2
    assert response_data["pagination"]["total_items"] == 2

    # Snapshot test the response
    snapshot.snapshot_dir = "snapshots"
    snapshot.assert_match(
        json.dumps(response_data, indent=2, sort_keys=True),
        "adm_usr_hist_ok",
    )
