async def test_form_user_pairing_fails(hass: HomeAssistant, tmp_path: Path) -> None:
    """Test we get the form and we handle pairing failure."""
    config_dir = tmp_path / "tls_assets"
    await hass.async_add_executor_job(config_dir.mkdir)
    hass.config.config_dir = str(config_dir)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None
    assert result["step_id"] == "user"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "1.1.1.1",
        },
    )
    await hass.async_block_till_done()
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "link"

    with (
        patch(
            "homeassistant.components.lutron_caseta.config_flow.async_pair",
            side_effect=TimeoutError,
        ),
        patch(
            "homeassistant.components.lutron_caseta.async_setup", return_value=True
        ) as mock_setup,
        patch(
            "homeassistant.components.lutron_caseta.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {},
        )
        await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.FORM
    assert result3["errors"] == {"base": "cannot_connect"}
    assert len(mock_setup.mock_calls) == 0
    assert len(mock_setup_entry.mock_calls) == 0