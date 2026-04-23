async def test_options_flow_drawables(
    hass: HomeAssistant, mock_roborock_entry: MockConfigEntry
) -> None:
    """Test that the options flow works."""
    with patch("homeassistant.components.roborock.roborock_storage"):
        await hass.config_entries.async_setup(mock_roborock_entry.entry_id)
        await hass.async_block_till_done()

        result = await hass.config_entries.options.async_init(
            mock_roborock_entry.entry_id
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == DRAWABLES
        with patch(
            "homeassistant.components.roborock.async_setup_entry", return_value=True
        ) as mock_setup:
            result = await hass.config_entries.options.async_configure(
                result["flow_id"],
                user_input={
                    Drawable.PREDICTED_PATH: True,
                    CONF_SHOW_ROOMS: True,
                    CONF_SHOW_WALLS: True,
                },
            )
            await hass.async_block_till_done()

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert mock_roborock_entry.options[DRAWABLES][Drawable.PREDICTED_PATH] is True
        assert mock_roborock_entry.options[CONF_SHOW_ROOMS] is True
        assert mock_roborock_entry.options[CONF_SHOW_WALLS] is True
        assert len(mock_setup.mock_calls) == 1