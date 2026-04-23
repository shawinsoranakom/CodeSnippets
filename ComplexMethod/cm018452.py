async def test_user_form(hass: HomeAssistant, doorbird_api: DoorBird) -> None:
    """Test we get the user form."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with (
        patch(
            "homeassistant.components.doorbird.async_setup", return_value=True
        ) as mock_setup,
        patch(
            "homeassistant.components.doorbird.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_CONFIG,
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "1.2.3.4"
    assert result2["data"] == {
        "host": "1.2.3.4",
        "name": "mydoorbird",
        "password": "password",
        "username": "friend",
    }
    assert result2["options"] == {
        CONF_EVENTS: [DEFAULT_DOORBELL_EVENT, DEFAULT_MOTION_EVENT]
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1