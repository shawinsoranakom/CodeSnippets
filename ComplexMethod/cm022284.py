async def test_user_form(hass: HomeAssistant) -> None:
    """Test the full user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=CONFIG,
    )
    assert result["type"] is FlowResultType.FORM

    with patch("os.path.isdir", return_value=False):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CONFIG,
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {"base": "directory_does_not_exist"}

    with (
        patch(
            "homeassistant.components.downloader.async_setup_entry", return_value=True
        ),
        patch(
            "os.path.isdir",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CONFIG,
        )
        await hass.async_block_till_done()
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == "Downloader"
        assert result["data"] == {"download_dir": "download_dir"}