async def test_clean_supervisor_discovery_on_user_create(
    hass: HomeAssistant,
    supervisor: MagicMock,
    addon_running: AsyncMock,
    addon_info: AsyncMock,
    client_connect: AsyncMock,
    setup_entry: AsyncMock,
) -> None:
    """Test discovery flow is cleaned up when a user flow is finished."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_HASSIO},
        data=HassioServiceInfo(
            config=ADDON_DISCOVERY_INFO,
            name="Matter Server",
            slug=ADDON_SLUG,
            uuid="1234",
        ),
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "hassio_confirm"

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "on_supervisor"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"use_addon": False}
    )

    assert addon_info.call_count == 0
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "manual"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "url": "ws://localhost:5580/ws",
        },
    )
    await hass.async_block_till_done()

    assert len(hass.config_entries.flow.async_progress()) == 0
    assert client_connect.call_count == 1
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Matter"
    assert result["data"] == {
        "url": "ws://localhost:5580/ws",
        "use_addon": False,
        "integration_created_addon": False,
    }
    assert setup_entry.call_count == 1