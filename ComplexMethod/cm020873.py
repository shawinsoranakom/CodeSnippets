async def test_validation_options(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test validation."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["step_id"] == "user"
    assert result["type"] is FlowResultType.FORM

    with (
        patch("os.path.isfile", Mock(return_value=True)),
        patch("os.access", Mock(return_value=False)),
        patch(
            "homeassistant.components.local_file.camera.mimetypes.guess_type",
            Mock(return_value=(None, None)),
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_NAME: DEFAULT_NAME,
                CONF_FILE_PATH: "mock.file",
            },
        )
        await hass.async_block_till_done()

    assert result["step_id"] == "user"
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "not_readable_path"}

    with (
        patch("os.path.isfile", Mock(return_value=True)),
        patch("os.access", Mock(return_value=True)),
        patch(
            "homeassistant.components.local_file.camera.mimetypes.guess_type",
            Mock(return_value=(None, None)),
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_NAME: DEFAULT_NAME,
                CONF_FILE_PATH: "mock.new.file",
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["version"] == 1
    assert result["options"] == {
        CONF_NAME: DEFAULT_NAME,
        CONF_FILE_PATH: "mock.new.file",
    }

    assert len(mock_setup_entry.mock_calls) == 1