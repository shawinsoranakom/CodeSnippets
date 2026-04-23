async def test_options_flow(hass: HomeAssistant) -> None:
    """Test updating options after setup."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_DATA,
        options=MOCK_OPTIONS,
    )
    mock_entry.add_to_hass(hass)

    new_options = {
        "prefix": "updated",
        "rate": 5,
    }

    # OSError Case
    with patch(
        "homeassistant.components.datadog.config_flow.DogStatsd",
        side_effect=OSError,
    ):
        result = await hass.config_entries.options.async_init(mock_entry.entry_id)
        assert result["type"] is FlowResultType.FORM
        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"], user_input=new_options
        )
        assert result2["type"] is FlowResultType.FORM
        assert result2["errors"] == {"base": "cannot_connect"}

    # ValueError Case
    with patch(
        "homeassistant.components.datadog.config_flow.DogStatsd",
        side_effect=ValueError,
    ):
        result = await hass.config_entries.options.async_init(mock_entry.entry_id)
        assert result["type"] is FlowResultType.FORM
        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"], user_input=new_options
        )
        assert result2["type"] is FlowResultType.FORM
        assert result2["errors"] == {"base": "cannot_connect"}

    # Success Case
    with patch(
        "homeassistant.components.datadog.config_flow.DogStatsd"
    ) as mock_dogstatsd:
        mock_instance = MagicMock()
        mock_dogstatsd.return_value = mock_instance

        result = await hass.config_entries.options.async_configure(
            result["flow_id"], user_input=new_options
        )

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"] == new_options
        mock_instance.increment.assert_called_once_with("connection_test")