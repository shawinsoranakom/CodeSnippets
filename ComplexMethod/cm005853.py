async def test_get_all_decrypted_variables(service, session: AsyncSession):
    """Test get_all_decrypted_variables returns all variables with decrypted values."""
    user_id = uuid4()

    # Create multiple variables with different types
    await service.create_variable(user_id, "API_KEY_1", "secret_value_1", type_=CREDENTIAL_TYPE, session=session)
    await service.create_variable(user_id, "API_KEY_2", "secret_value_2", type_=CREDENTIAL_TYPE, session=session)
    await service.create_variable(user_id, "GENERIC_VAR", "plain_value", type_="GENERIC", session=session)

    # Get all decrypted variables
    result = await service.get_all_decrypted_variables(user_id, session=session)

    # Verify all variables are returned
    assert len(result) == 3
    assert "API_KEY_1" in result
    assert "API_KEY_2" in result
    assert "GENERIC_VAR" in result

    # Verify values are decrypted
    assert result["API_KEY_1"] == "secret_value_1"  # pragma: allowlist secret
    assert result["API_KEY_2"] == "secret_value_2"  # pragma: allowlist secret
    assert result["GENERIC_VAR"] == "plain_value"