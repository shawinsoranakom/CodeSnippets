async def test_form_uuid_not_provided_by_api(hass: HomeAssistant) -> None:
    """Test we get the form, but uuid is missing from the all API messages."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with (
        patch(
            "homeassistant.components.lg_soundbar.config_flow.QUEUE_TIMEOUT",
            new=0.1,
        ),
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
            product_info={"i_model_no": "8", "i_model_type": 0},
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
    assert result2["result"].unique_id is None
    assert result2["data"] == {
        CONF_HOST: "1.1.1.1",
        CONF_PORT: DEFAULT_PORT,
    }
    assert len(mock_setup_entry.mock_calls) == 1