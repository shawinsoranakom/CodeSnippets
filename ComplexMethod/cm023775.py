async def test_hassio_addon_discovery(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    snapshot: SnapshotAssertion,
    info: Info,
) -> None:
    """Test config flow initiated by Supervisor."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=ADDON_DISCOVERY,
        context={"source": config_entries.SOURCE_HASSIO},
    )

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "hassio_confirm"
    assert result.get("description_placeholders") == {"addon": "Piper"}

    with patch(
        "homeassistant.components.wyoming.data.load_wyoming_info",
        return_value=info,
    ) as mock_wyoming:
        result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    assert result2.get("type") is FlowResultType.CREATE_ENTRY
    assert result2 == snapshot

    assert len(mock_setup_entry.mock_calls) == 1
    assert len(mock_wyoming.mock_calls) == 1