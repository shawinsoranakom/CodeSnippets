async def test_subentry_switching(
    hass: HomeAssistant,
    mock_config_entry,
    mock_init_component,
    current_options,
    new_options,
    expected_options,
) -> None:
    """Test the subentry form."""
    subentry = next(
        sub
        for sub in mock_config_entry.subentries.values()
        if sub.subentry_type == "conversation"
    )
    hass.config_entries.async_update_subentry(
        mock_config_entry, subentry, data=current_options
    )
    await hass.async_block_till_done()
    subentry_flow = await mock_config_entry.start_subentry_reconfigure_flow(
        hass, subentry.subentry_id
    )
    assert subentry_flow["step_id"] == "init"

    for step_options in new_options:
        assert subentry_flow["type"] is FlowResultType.FORM

        # Test that current options are showed as suggested values:
        for key in subentry_flow["data_schema"].schema:
            if (
                isinstance(key.description, dict)
                and "suggested_value" in key.description
                and key in current_options
            ):
                current_option = current_options[key]
                if key == CONF_LLM_HASS_API and isinstance(current_option, str):
                    current_option = [current_option]
                assert key.description["suggested_value"] == current_option

        # Configure current step
        subentry_flow = await hass.config_entries.subentries.async_configure(
            subentry_flow["flow_id"],
            step_options,
        )
        await hass.async_block_till_done()

    assert subentry_flow["type"] is FlowResultType.ABORT
    assert subentry_flow["reason"] == "reconfigure_successful"
    assert subentry.data == expected_options