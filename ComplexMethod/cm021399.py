async def test_form(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_hikcamera: MagicMock,
) -> None:
    """Test we get the form and can create entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: TEST_HOST,
            CONF_PORT: TEST_PORT,
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_SSL: False,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TEST_DEVICE_NAME
    assert result["result"].unique_id == TEST_DEVICE_ID
    assert result["data"] == {
        CONF_HOST: TEST_HOST,
        CONF_PORT: TEST_PORT,
        CONF_USERNAME: TEST_USERNAME,
        CONF_PASSWORD: TEST_PASSWORD,
        CONF_SSL: False,
    }

    # Verify HikCamera was called with the ssl parameter
    mock_hikcamera.assert_called_once_with(
        f"http://{TEST_HOST}", TEST_PORT, TEST_USERNAME, TEST_PASSWORD, False
    )