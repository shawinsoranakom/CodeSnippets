async def test_multiple_flow_implementation(hass: HomeAssistant) -> None:
    """Test multiple device flows."""
    # User Step Started, results in Step Creds
    with patch("pyps4_2ndscreen.Helper.port_bind", return_value=None):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "creds"

    # Step Creds results with form in Step Mode.
    with patch("pyps4_2ndscreen.Helper.get_creds", return_value=MOCK_CREDS):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "mode"

    # Step Mode with User Input which is not manual, results in Step Link.
    with patch(
        "pyps4_2ndscreen.Helper.has_devices",
        return_value=[{"host-ip": MOCK_HOST}, {"host-ip": MOCK_HOST_ADDITIONAL}],
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_AUTO
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "link"

    # User Input results in created entry.
    with (
        patch("pyps4_2ndscreen.Helper.link", return_value=(True, True)),
        patch(
            "pyps4_2ndscreen.Helper.has_devices",
            return_value=[{"host-ip": MOCK_HOST}, {"host-ip": MOCK_HOST_ADDITIONAL}],
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_CONFIG
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_TOKEN] == MOCK_CREDS
    assert result["data"]["devices"] == [MOCK_DEVICE]
    assert result["title"] == MOCK_TITLE

    # Check if entry exists.
    entries = hass.config_entries.async_entries()
    assert len(entries) == 1
    # Check if there is a device config in entry.
    entry_1 = entries[0]
    assert len(entry_1.data["devices"]) == 1

    # Test additional flow.

    # User Step Started, results in Step Mode:
    with (
        patch("pyps4_2ndscreen.Helper.port_bind", return_value=None),
        patch(
            "pyps4_2ndscreen.Helper.has_devices",
            return_value=[{"host-ip": MOCK_HOST}, {"host-ip": MOCK_HOST_ADDITIONAL}],
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "creds"

    # Step Creds results with form in Step Mode.
    with patch("pyps4_2ndscreen.Helper.get_creds", return_value=MOCK_CREDS):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "mode"

    # Step Mode with User Input which is not manual, results in Step Link.
    with patch(
        "pyps4_2ndscreen.Helper.has_devices",
        return_value=[{"host-ip": MOCK_HOST}, {"host-ip": MOCK_HOST_ADDITIONAL}],
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_AUTO
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "link"

    # Step Link
    with (
        patch(
            "pyps4_2ndscreen.Helper.has_devices",
            return_value=[{"host-ip": MOCK_HOST}, {"host-ip": MOCK_HOST_ADDITIONAL}],
        ),
        patch("pyps4_2ndscreen.Helper.link", return_value=(True, True)),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_CONFIG_ADDITIONAL
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_TOKEN] == MOCK_CREDS
    assert len(result["data"]["devices"]) == 1
    assert result["title"] == MOCK_TITLE

    # Check if there are 2 entries.
    entries = hass.config_entries.async_entries()
    assert len(entries) == 2
    # Check if there is device config in the last entry.
    entry_2 = entries[-1]
    assert len(entry_2.data["devices"]) == 1

    # Check that entry 1 is different from entry 2.
    assert entry_1 is not entry_2