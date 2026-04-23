async def test_option_flow(
    hass: HomeAssistant,
    parameter: str,
    initial: list[str],
    suggested: str | list[str],
    user_input: str | list[str],
    updated: list[str],
) -> None:
    """Test config flow options."""
    basic_parameters = ["known_hosts"]
    advanced_parameters = ["ignore_cec", "uuid"]

    data = {
        "ignore_cec": [],
        "known_hosts": [],
        "uuid": [],
    }
    data[parameter] = initial
    config_entry = MockConfigEntry(domain="cast", data=data)
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Test ignore_cec and uuid options are hidden if advanced options are disabled
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "basic_options"
    data_schema = result["data_schema"].schema
    assert set(data_schema) == {"known_hosts"}
    orig_data = dict(config_entry.data)

    # Reconfigure known_hosts
    context = {"source": config_entries.SOURCE_USER, "show_advanced_options": True}
    result = await hass.config_entries.options.async_init(
        config_entry.entry_id, context=context
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "basic_options"
    data_schema = result["data_schema"].schema
    for other_param in basic_parameters:
        if other_param == parameter:
            continue
        assert get_schema_suggested_value(data_schema, other_param) == []
    if parameter in basic_parameters:
        assert get_schema_suggested_value(data_schema, parameter) == suggested

    user_input_dict = {}
    if parameter in basic_parameters:
        user_input_dict[parameter] = user_input
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input=user_input_dict,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "advanced_options"
    for other_param in basic_parameters:
        if other_param == parameter:
            continue
        assert config_entry.data[other_param] == []
    # No update yet
    assert config_entry.data[parameter] == initial

    # Reconfigure ignore_cec, uuid
    data_schema = result["data_schema"].schema
    for other_param in advanced_parameters:
        if other_param == parameter:
            continue
        assert get_schema_suggested_value(data_schema, other_param) == ""
    if parameter in advanced_parameters:
        assert get_schema_suggested_value(data_schema, parameter) == suggested

    user_input_dict = {}
    if parameter in advanced_parameters:
        user_input_dict[parameter] = user_input
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input=user_input_dict,
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {}
    for other_param in advanced_parameters:
        if other_param == parameter:
            continue
        assert config_entry.data[other_param] == []
    assert config_entry.data[parameter] == updated

    # Clear known_hosts
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {}
    expected_data = {**orig_data, "known_hosts": []}
    if parameter in advanced_parameters:
        expected_data[parameter] = updated
    assert dict(config_entry.data) == expected_data