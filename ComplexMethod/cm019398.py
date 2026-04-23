async def test_update_device(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_smile_adam_heat_cool: MagicMock,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test a clean-up of the device_registry."""
    data = mock_smile_adam_heat_cool.async_update.return_value

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert (
        len(
            er.async_entries_for_config_entry(
                entity_registry, mock_config_entry.entry_id
            )
        )
        == 56
    )
    assert (
        len(
            dr.async_entries_for_config_entry(
                device_registry, mock_config_entry.entry_id
            )
        )
        == 11
    )

    # Add a 2nd Tom/Floor
    data.update(TOM)
    data["f871b8c4d63549319221e294e4f88074"]["thermostats"].update(
        {
            "secondary": [
                "01234567890abcdefghijklmnopqrstu",
                "1772a4ea304041adb83f357b751341ff",
            ]
        }
    )
    with patch(HA_PLUGWISE_SMILE_ASYNC_UPDATE, return_value=data):
        freezer.tick(timedelta(minutes=1))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

        assert (
            len(
                er.async_entries_for_config_entry(
                    entity_registry, mock_config_entry.entry_id
                )
            )
            == 63
        )
        assert (
            len(
                dr.async_entries_for_config_entry(
                    device_registry, mock_config_entry.entry_id
                )
            )
            == 12
        )
        device_entry = device_registry.async_get_device(
            identifiers={(DOMAIN, "01234567890abcdefghijklmnopqrstu")}
        )
        assert device_entry is not None

    # Remove the existing Tom/Floor
    data["f871b8c4d63549319221e294e4f88074"]["thermostats"].update(
        {"secondary": ["01234567890abcdefghijklmnopqrstu"]}
    )
    data.pop("1772a4ea304041adb83f357b751341ff")
    with patch(HA_PLUGWISE_SMILE_ASYNC_UPDATE, return_value=data):
        freezer.tick(timedelta(minutes=1))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

        assert (
            len(
                er.async_entries_for_config_entry(
                    entity_registry, mock_config_entry.entry_id
                )
            )
            == 56
        )
        assert (
            len(
                dr.async_entries_for_config_entry(
                    device_registry, mock_config_entry.entry_id
                )
            )
            == 11
        )
        device_entry = device_registry.async_get_device(
            identifiers={(DOMAIN, "1772a4ea304041adb83f357b751341ff")}
        )
        assert device_entry is None