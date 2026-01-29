def test_configure_auto_top_up_validation_errors(
    mocker: pytest_mock.MockFixture,
) -> None:
    """Test configure auto top-up endpoint validation"""
    # Mock set_auto_top_up to avoid database operations for successful case
    mocker.patch("backend.api.features.v1.set_auto_top_up")

    # Mock credit model to avoid Stripe API calls for the successful case
    mock_credit_model = mocker.AsyncMock()
    mock_credit_model.get_credits.return_value = 50
    mock_credit_model.top_up_credits.return_value = None

    mocker.patch(
        "backend.api.features.v1.get_user_credit_model",
        return_value=mock_credit_model,
    )

    # Test negative threshold
    response = client.post(
        "/credits/auto-top-up", json={"threshold": -1, "amount": 500}
    )
    assert response.status_code == 422  # Validation error

    # Test amount too small (but not 0)
    response = client.post(
        "/credits/auto-top-up", json={"threshold": 100, "amount": 100}
    )
    assert response.status_code == 422  # Validation error

    # Test amount = 0 (should be allowed)
    response = client.post("/credits/auto-top-up", json={"threshold": 100, "amount": 0})
    assert response.status_code == 200  # Should succeed
