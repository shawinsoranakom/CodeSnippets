async def test_form_user_doorbird_not_found(
    doorbird_api: DoorBird, hass: HomeAssistant
) -> None:
    """Test handling unable to connect to the device."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_error = mock_not_found_exception()
    doorbirdapi = get_mock_doorbird_api(info_side_effect=mock_error)
    with patch(
        "homeassistant.components.doorbird.config_flow.DoorBird",
        return_value=doorbirdapi,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_CONFIG,
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}

    with (
        patch(
            "homeassistant.components.doorbird.async_setup", return_value=True
        ) as mock_setup,
        patch(
            "homeassistant.components.doorbird.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"], VALID_CONFIG
        )
        await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"] == "1.2.3.4"
    assert result3["data"] == {
        "host": "1.2.3.4",
        "name": "mydoorbird",
        "password": "password",
        "username": "friend",
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1