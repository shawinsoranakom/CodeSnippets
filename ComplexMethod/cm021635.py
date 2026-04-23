async def test_full_flow_implementation(hass: HomeAssistant) -> None:
    """Test registering an implementation and flow works."""
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
        "pyps4_2ndscreen.Helper.has_devices", return_value=[{"host-ip": MOCK_HOST}]
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
            "pyps4_2ndscreen.Helper.has_devices", return_value=[{"host-ip": MOCK_HOST}]
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_CONFIG
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_TOKEN] == MOCK_CREDS
    assert result["data"]["devices"] == [MOCK_DEVICE]
    assert result["title"] == MOCK_TITLE