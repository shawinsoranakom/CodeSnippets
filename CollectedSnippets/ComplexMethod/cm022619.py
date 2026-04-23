async def test_hassio_success(hass: HomeAssistant) -> None:
    """Test successful Supervisor flow."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=HassioServiceInfo(
            config={"addon": "motionEye", "url": TEST_URL},
            name="motionEye",
            slug="motioneye",
            uuid="1234",
        ),
        context={"source": config_entries.SOURCE_HASSIO},
    )

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "hassio_confirm"
    assert result.get("description_placeholders") == {"addon": "motionEye"}

    result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result2.get("type") is FlowResultType.FORM
    assert result2.get("step_id") == "user"

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
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {
                CONF_ADMIN_USERNAME: "admin-username",
                CONF_ADMIN_PASSWORD: "admin-password",
                CONF_SURVEILLANCE_USERNAME: "surveillance-username",
                CONF_SURVEILLANCE_PASSWORD: "surveillance-password",
            },
        )
        await hass.async_block_till_done()

    assert result3.get("type") is FlowResultType.CREATE_ENTRY
    assert result3.get("title") == "App"
    assert result3.get("data") == {
        CONF_URL: TEST_URL,
        CONF_ADMIN_USERNAME: "admin-username",
        CONF_ADMIN_PASSWORD: "admin-password",
        CONF_SURVEILLANCE_USERNAME: "surveillance-username",
        CONF_SURVEILLANCE_PASSWORD: "surveillance-password",
    }
    assert len(mock_setup_entry.mock_calls) == 1
    assert mock_client.async_client_close.called