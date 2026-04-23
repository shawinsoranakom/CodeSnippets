async def test_zeroconf_during_onboarding(
    hass: HomeAssistant, local_devices: Any
) -> None:
    """Test the zeroconf creates an entry during onboarding."""
    with (
        patch(
            "homeassistant.components.awair.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
        patch("python_awair.AwairClient.query", side_effect=[local_devices]),
        patch(
            "homeassistant.components.onboarding.async_is_onboarded",
            return_value=False,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_ZEROCONF}, data=ZEROCONF_DISCOVERY
        )

    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert result.get("title") == "Awair Element (24947)"
    assert "data" in result
    assert result["data"][CONF_HOST] == ZEROCONF_DISCOVERY.host
    assert "result" in result
    assert result["result"].unique_id == LOCAL_UNIQUE_ID
    assert len(mock_setup_entry.mock_calls) == 1