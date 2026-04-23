async def test_update_table_params_with_load_from_db_fields_basic():
    """Test basic table load_from_db functionality."""
    # Create mock custom component
    custom_component = MagicMock()

    # Mock database values
    async def mock_get_variable(name, **_kwargs):
        mock_values = {
            "ADMIN_USER": "actual_admin_user",
            "ADMIN_EMAIL": "admin@company.com",
        }
        if name in mock_values:
            return mock_values[name]
        msg = f"{name} variable not found."
        raise ValueError(msg)

    custom_component.get_variable = AsyncMock(side_effect=mock_get_variable)

    # Set up table params
    params = {
        "table_data": [
            {"username": "ADMIN_USER", "email": "ADMIN_EMAIL", "role": "admin"},
            {"username": "static_user", "email": "static@example.com", "role": "user"},
        ],
        "table_data_load_from_db_columns": ["username", "email"],
    }

    # Call the function
    with patch("lfx.interface.initialize.loading.session_scope") as mock_session_scope:
        mock_session_scope.return_value.__aenter__.return_value = MagicMock()

        result = await update_table_params_with_load_from_db_fields(
            custom_component, params, "table_data", fallback_to_env_vars=False
        )

    # Check results
    table_data = result["table_data"]
    assert len(table_data) == 2

    # First row should have resolved values
    assert table_data[0]["username"] == "actual_admin_user"
    assert table_data[0]["email"] == "admin@company.com"
    assert table_data[0]["role"] == "admin"  # unchanged

    # Second row should have None for variables not found
    assert table_data[1]["username"] is None  # static_user not in mock DB
    assert table_data[1]["email"] is None  # static@example.com not in mock DB
    assert table_data[1]["role"] == "user"  # unchanged

    # Metadata should be removed
    assert "table_data_load_from_db_columns" not in result