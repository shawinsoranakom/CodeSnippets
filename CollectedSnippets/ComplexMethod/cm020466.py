async def test_form_uuid_present_in_both_functions_uuid_q_empty(
    hass: HomeAssistant,
) -> None:
    """Get the form, uuid present in both get_mac_info and get_product_info calls.

    Value from get_mac_info is not added to uuid_q before get_product_info is run.
    """

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with (
        patch(
            "homeassistant.components.lg_soundbar.config_flow.temescal"
        ) as mock_temescal,
        patch(
            "homeassistant.components.lg_soundbar.async_setup_entry", return_value=True
        ) as mock_setup_entry,
    ):
        setup_mock_temescal(
            hass=hass,
            mock_temescal=mock_temescal,
            mac_info_dev={"s_uuid": "uuid"},
            product_info={"s_uuid": "uuid"},
            info={"s_user_name": "name"},
        )

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "name"
    assert result2["result"].unique_id == "uuid"
    assert result2["data"] == {
        CONF_HOST: "1.1.1.1",
        CONF_PORT: DEFAULT_PORT,
    }
    assert len(mock_setup_entry.mock_calls) == 1