async def test_creating_entry_removes_entries_for_same_host_or_bridge(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test that we clean up entries for same host and bridge.

    An IP can only hold a single bridge and a single bridge can only be
    accessible via a single IP. So when we create a new entry, we'll remove
    all existing entries that either have same IP or same bridge_id.
    """
    create_mock_api_discovery(aioclient_mock, [("2.2.2.2", "id-1234")])
    orig_entry = MockConfigEntry(
        domain="hue",
        data={"host": "0.0.0.0", "api_key": "123456789"},
        unique_id="id-1234",
    )
    orig_entry.add_to_hass(hass)

    MockConfigEntry(
        domain="hue",
        data={"host": "1.2.3.4", "api_key": "123456789"},
        unique_id="id-5678",
    ).add_to_hass(hass)

    assert len(hass.config_entries.async_entries("hue")) == 2

    result = await hass.config_entries.flow.async_init(
        "hue",
        data={"host": "2.2.2.2"},
        context={"source": config_entries.SOURCE_IMPORT},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "link"

    with (
        patch(
            "homeassistant.components.hue.config_flow.create_app_key",
            return_value="123456789",
        ),
        patch("homeassistant.components.hue.async_unload_entry", return_value=True),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Hue Bridge id-1234"
    assert result["data"] == {
        "host": "2.2.2.2",
        "api_key": "123456789",
        "api_version": 1,
    }
    entries = hass.config_entries.async_entries("hue")
    assert len(entries) == 2
    new_entry = entries[-1]
    assert orig_entry.entry_id != new_entry.entry_id
    assert new_entry.unique_id == "id-1234"