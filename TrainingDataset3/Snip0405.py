def test_add_user_credits_success(
    mocker: pytest_mock.MockerFixture,
    configured_snapshot: Snapshot,
    admin_user_id: str,
    target_user_id: str,
) -> None:
    """Test successful credit addition by admin"""
    # Mock the credit model
    mock_credit_model = Mock()
    mock_credit_model._add_transaction = AsyncMock(
        return_value=(1500, "transaction-123-uuid")
    )
    mocker.patch(
        "backend.api.features.admin.credit_admin_routes.get_user_credit_model",
        return_value=mock_credit_model,
    )

    request_data = {
        "user_id": target_user_id,
        "amount": 500,
        "comments": "Test credit grant for debugging",
    }

    response = client.post("/admin/add_credits", json=request_data)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["new_balance"] == 1500
    assert response_data["transaction_key"] == "transaction-123-uuid"

    # Verify the function was called with correct parameters
    mock_credit_model._add_transaction.assert_called_once()
    call_args = mock_credit_model._add_transaction.call_args
    assert call_args[0] == (target_user_id, 500)
    assert call_args[1]["transaction_type"] == prisma.enums.CreditTransactionType.GRANT
    # Check that metadata is a SafeJson object with the expected content
    assert isinstance(call_args[1]["metadata"], SafeJson)
    actual_metadata = call_args[1]["metadata"]
    expected_data = {
        "admin_id": admin_user_id,
        "reason": "Test credit grant for debugging",
    }

    # SafeJson inherits from Json which stores parsed data in the .data attribute
    assert actual_metadata.data["admin_id"] == expected_data["admin_id"]
    assert actual_metadata.data["reason"] == expected_data["reason"]

    # Snapshot test the response
    configured_snapshot.assert_match(
        json.dumps(response_data, indent=2, sort_keys=True),
        "admin_add_credits_success",
    )
