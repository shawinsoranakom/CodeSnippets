async def test_flow_fails_on_validation(hass: HomeAssistant, tmp_path: Path) -> None:
    """Test config flow errors."""
    test_file = str(tmp_path.joinpath(TEST_FILE_NAME))
    hass.config.allowlist_external_dirs = {}

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_FILE_PATH: test_file,
        },
    )

    assert result2["errors"] == {"base": "not_valid"}

    await async_create_file(hass, test_file)

    with patch(
        "homeassistant.components.filesize.config_flow.pathlib.Path",
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_FILE_PATH: test_file,
            },
        )

    assert result2["errors"] == {"base": "not_allowed"}

    hass.config.allowlist_external_dirs = {tmp_path}
    with patch(
        "homeassistant.components.filesize.config_flow.pathlib.Path",
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_FILE_PATH: test_file,
            },
        )

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == TEST_FILE_NAME
    assert result2["data"] == {
        CONF_FILE_PATH: test_file,
    }