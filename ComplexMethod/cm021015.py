async def test_full_flow_implementation(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test registering an integration and finishing flow works."""
    aioclient_mock.get(
        (
            f"{'https' if FIXTURE_USER_INPUT[CONF_SSL] else 'http'}"
            f"://{FIXTURE_USER_INPUT[CONF_HOST]}"
            f":{FIXTURE_USER_INPUT[CONF_PORT]}/control/status"
        ),
        json={"version": "v0.99.0"},
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result
    assert result["flow_id"]
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=FIXTURE_USER_INPUT
    )
    assert result
    assert result["type"] is FlowResultType.CREATE_ENTRY

    config_entry = result["result"]
    assert config_entry.title == FIXTURE_USER_INPUT[CONF_HOST]
    assert config_entry.data == {
        CONF_HOST: FIXTURE_USER_INPUT[CONF_HOST],
        CONF_PASSWORD: FIXTURE_USER_INPUT[CONF_PASSWORD],
        CONF_PORT: FIXTURE_USER_INPUT[CONF_PORT],
        CONF_SSL: FIXTURE_USER_INPUT[CONF_SSL],
        CONF_USERNAME: FIXTURE_USER_INPUT[CONF_USERNAME],
        CONF_VERIFY_SSL: FIXTURE_USER_INPUT[CONF_VERIFY_SSL],
    }
    assert not config_entry.options