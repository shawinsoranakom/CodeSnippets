async def test_already_configured_device(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test we handle invalid auth."""
    mock_config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "username": "test-username",
            "password": "test-password",
            "id": "1",
            "name": "Test",
        },
        unique_id="1",
    )
    mock_config_entry.add_to_hass(hass)

    # Now that we did the config once, let's try to do it again, this should raise the abort for already configured device

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None

    with (
        patch(
            "lacrosse_view.LaCrosse.login",
            return_value=True,
        ),
        patch(
            "lacrosse_view.LaCrosse.get_locations",
            return_value=[Location(id="1", name="Test")],
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "test-password",
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "location"
    assert result2["errors"] is None

    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        {
            "location": "1",
        },
    )
    await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.ABORT
    assert result3["reason"] == "already_configured"
    assert len(mock_setup_entry.mock_calls) == 0