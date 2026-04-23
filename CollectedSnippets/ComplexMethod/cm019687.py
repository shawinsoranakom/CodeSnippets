async def test_reconfigure_nonsecure(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test reconfigure flow switching to non-secure protocol."""
    # Add mock_config_entry to hass before updating
    mock_config_entry.add_to_hass(hass)

    # Update mock_config_entry.data using async_update_entry
    hass.config_entries.async_update_entry(
        mock_config_entry,
        data={
            CONF_AUTO_CONFIGURE: True,
            CONF_HOST: "elk://localhost",
            CONF_USERNAME: "",
            CONF_PASSWORD: "",
            CONF_PREFIX: "",
        },
    )

    await hass.async_block_till_done()

    result = await mock_config_entry.start_reconfigure_flow(hass)
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    # Mock elk library to simulate successful connection
    mocked_elk = mock_elk(invalid_auth=False, sync_complete=True)

    with (
        _patch_discovery(no_device=True),
        _patch_elk(mocked_elk),
        patch(
            "homeassistant.components.elkm1.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_PROTOCOL: "non-secure",
                CONF_ADDRESS: "1.2.3.4",
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "reconfigure_successful"

    # Verify the config entry was updated with the new data
    assert dict(mock_config_entry.data) == {
        CONF_AUTO_CONFIGURE: True,
        CONF_HOST: "elk://1.2.3.4",
        CONF_USERNAME: "",
        CONF_PASSWORD: "",
        CONF_PREFIX: "",
    }

    # Verify the setup was called during reload
    mock_setup_entry.assert_called_once()

    # Verify the elk library was initialized and connected
    assert mocked_elk.connect.call_count == 1
    assert mocked_elk.disconnect.call_count == 1