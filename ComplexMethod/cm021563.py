async def test_options_flow_with_no_selection(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_config_entry: MockConfigEntry,
    mock_nina_class: AsyncMock,
    nina_warnings: list[Warning],
) -> None:
    """Test config flow options with no selection."""
    await setup_platform(hass, mock_config_entry, mock_nina_class, nina_warnings)

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONST_REGION_A_TO_D: [],
            CONST_REGION_E_TO_H: [],
            CONST_REGION_I_TO_L: [],
            CONST_REGION_M_TO_Q: [],
            CONST_REGION_R_TO_U: [],
            CONST_REGION_V_TO_Z: [],
            CONF_FILTERS: {CONF_HEADLINE_FILTER: ""},
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    assert result["errors"] == {"base": "no_selection"}

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONST_REGION_A_TO_D: ["095760000000_0"],
            CONST_REGION_E_TO_H: [],
            CONST_REGION_I_TO_L: [],
            CONST_REGION_M_TO_Q: [],
            CONST_REGION_R_TO_U: [],
            CONST_REGION_V_TO_Z: [],
            CONF_FILTERS: {
                CONF_HEADLINE_FILTER: ".*corona.*",
                CONF_AREA_FILTER: ".*",
            },
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {}

    assert dict(mock_config_entry.data) == {
        CONF_FILTERS: DUMMY_USER_INPUT[CONF_FILTERS],
        CONF_MESSAGE_SLOTS: DUMMY_USER_INPUT[CONF_MESSAGE_SLOTS],
        CONST_REGION_A_TO_D: ["095760000000_0"],
        CONST_REGION_E_TO_H: [],
        CONST_REGION_I_TO_L: [],
        CONST_REGION_M_TO_Q: [],
        CONST_REGION_R_TO_U: [],
        CONST_REGION_V_TO_Z: [],
        CONF_REGIONS: {"095760000000": "Allersberg, M (Roth - Bayern)"},
    }