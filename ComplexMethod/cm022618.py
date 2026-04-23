async def test_user_success(hass: HomeAssistant) -> None:
    """Test successful user flow."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert not result["errors"]

    mock_client = create_mock_motioneye_client()

    with (
        patch(
            "homeassistant.components.motioneye.MotionEyeClient",
            return_value=mock_client,
        ),
        patch(
            "homeassistant.components.motioneye.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_URL: TEST_URL,
                CONF_ADMIN_USERNAME: "admin-username",
                CONF_ADMIN_PASSWORD: "admin-password",
                CONF_SURVEILLANCE_USERNAME: "surveillance-username",
                CONF_SURVEILLANCE_PASSWORD: "surveillance-password",
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == f"{TEST_URL}"
    assert result["data"] == {
        CONF_URL: TEST_URL,
        CONF_ADMIN_USERNAME: "admin-username",
        CONF_ADMIN_PASSWORD: "admin-password",
        CONF_SURVEILLANCE_USERNAME: "surveillance-username",
        CONF_SURVEILLANCE_PASSWORD: "surveillance-password",
    }
    assert len(mock_setup_entry.mock_calls) == 1
    assert mock_client.async_client_close.called