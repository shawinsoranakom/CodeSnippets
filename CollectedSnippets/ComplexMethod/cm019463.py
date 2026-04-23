async def test_reconfigure_step(
    hass: HomeAssistant,
    mock_process_uploaded_file: MagicMock,
    config_entry: MockConfigEntry,
) -> None:
    """Testcase for the reconfigure step."""
    await init_integration(hass, config_entry)
    result = await config_entry.start_reconfigure_flow(hass)
    assert result
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "network"

    # Submit the network step with the same host/port
    result = await hass.config_entries.flow.async_configure(
        result.get("flow_id"),
        {
            CONF_TLS: False,
            CONF_HOST: "127.0.1.0.1",
            CONF_PORT: 3788,
            CONF_PASSWORD: "",
        },
    )
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "vlp"

    with (
        patch(
            "velbusaio.vlp_reader.VlpFile.read",
            AsyncMock(return_value=True),
        ),
        patch(
            "velbusaio.vlp_reader.VlpFile.get",
            return_value=[1, 2, 3, 4],
        ),
    ):
        file_id = mock_process_uploaded_file.file_id
        result = await hass.config_entries.flow.async_configure(
            result.get("flow_id"),
            {CONF_VLP_FILE: file_id[CONF_VLP_FILE]},
        )
        await hass.async_block_till_done()

    assert result.get("type") is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"