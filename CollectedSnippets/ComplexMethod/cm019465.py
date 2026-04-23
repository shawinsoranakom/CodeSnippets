async def test_reconfigure_step_password_preserved(
    hass: HomeAssistant,
    mock_process_uploaded_file: MagicMock,
) -> None:
    """Test that an existing password is pre-filled and preserved during reconfigure."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_PORT: "tls://secret@192.168.0.1:27015"},
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await entry.start_reconfigure_flow(hass)
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "network"
    # Verify the password is pre-filled in the suggested values
    assert result["data_schema"](
        {
            CONF_TLS: True,
            CONF_HOST: "192.168.0.1",
            CONF_PORT: 27015,
            CONF_PASSWORD: "secret",
        }
    )

    # Submit without changing the password
    result = await hass.config_entries.flow.async_configure(
        result.get("flow_id"),
        {
            CONF_TLS: True,
            CONF_HOST: "192.168.0.1",
            CONF_PORT: 27015,
            CONF_PASSWORD: "secret",
        },
    )
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "vlp"

    with (
        patch("velbusaio.vlp_reader.VlpFile.read", AsyncMock(return_value=True)),
        patch("velbusaio.vlp_reader.VlpFile.get", return_value=[1, 2, 3, 4]),
    ):
        result = await hass.config_entries.flow.async_configure(
            result.get("flow_id"),
            {},
        )
        await hass.async_block_till_done()

    assert result.get("type") is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data[CONF_PORT] == "tls://secret@192.168.0.1:27015"