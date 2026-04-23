async def test_user_rest_auth(hass: HomeAssistant, mock_pyiskra_rest) -> None:
    """Test the user flow with Rest API protocol and authentication required."""
    mock_pyiskra_rest.side_effect = NotAuthorised

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    # Test if user form is provided
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # Test if prompted to enter username and password if not authorised
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: HOST, CONF_PROTOCOL: "rest_api"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "authentication"

    # Test failed authentication
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}
    assert result["step_id"] == "authentication"

    # Test successful authentication
    mock_pyiskra_rest.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
    )

    # Test successful Rest API configuration
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == SERIAL
    assert result["title"] == SG_MODEL
    assert result["data"] == {
        CONF_HOST: HOST,
        CONF_PROTOCOL: "rest_api",
        CONF_USERNAME: USERNAME,
        CONF_PASSWORD: PASSWORD,
    }