async def test_show_config_form_validate_webhook_not_connected(
    hass: HomeAssistant, webhook_id
) -> None:
    """Test validating webhook when not connected aborts."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_DEVICE_TYPE: PlaatoDeviceType.Airlock,
            CONF_DEVICE_NAME: "device_name",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "api_method"

    assert await async_setup_component(hass, "cloud", {})
    with (
        patch(
            "homeassistant.components.cloud.async_active_subscription",
            return_value=True,
        ),
        patch("homeassistant.components.cloud.async_is_logged_in", return_value=True),
        patch("homeassistant.components.cloud.async_is_connected", return_value=False),
        patch(
            "hass_nabucasa.cloudhooks.Cloudhooks.async_create",
            return_value={"cloudhook_url": "https://hooks.nabu.casa/ABCD"},
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_TOKEN: "",
                CONF_USE_WEBHOOK: True,
            },
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "cloud_not_connected"