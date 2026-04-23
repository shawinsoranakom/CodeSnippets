async def test_subentry_options_switching(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    current_options,
    new_options,
    expected_options,
    errors,
) -> None:
    """Test the options form."""
    subentry = next(iter(mock_config_entry.subentries.values()))
    with patch("google.genai.models.AsyncModels.get"):
        hass.config_entries.async_update_subentry(
            mock_config_entry, subentry, data=current_options
        )
        await hass.async_block_till_done()
    with patch(
        "google.genai.models.AsyncModels.list",
        return_value=get_models_pager(),
    ):
        options_flow = await mock_config_entry.start_subentry_reconfigure_flow(
            hass, subentry.subentry_id
        )
    if will_options_be_rendered_again(current_options, new_options):
        retry_options = {
            **current_options,
            CONF_RECOMMENDED: new_options[CONF_RECOMMENDED],
        }
        with patch(
            "google.genai.models.AsyncModels.list",
            return_value=get_models_pager(),
        ):
            options_flow = await hass.config_entries.subentries.async_configure(
                options_flow["flow_id"],
                retry_options,
            )
    with patch(
        "google.genai.models.AsyncModels.list",
        return_value=get_models_pager(),
    ):
        options = await hass.config_entries.subentries.async_configure(
            options_flow["flow_id"],
            new_options,
        )
        await hass.async_block_till_done()
    if errors is None:
        assert options["type"] is FlowResultType.ABORT
        assert options["reason"] == "reconfigure_successful"
        assert subentry.data == expected_options

    else:
        assert options["type"] is FlowResultType.FORM
    assert options.get("errors", None) == errors