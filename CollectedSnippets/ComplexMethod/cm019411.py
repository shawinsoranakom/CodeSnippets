async def test_full_user_flow(
    hass: HomeAssistant,
    mock_mjpeg_requests: Mocker,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test the full user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "user"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Spy cam",
            CONF_MJPEG_URL: "https://example.com/mjpeg",
            CONF_STILL_IMAGE_URL: "https://example.com/still",
            CONF_USERNAME: "frenck",
            CONF_PASSWORD: "omgpuppies",
            CONF_VERIFY_SSL: False,
        },
    )

    assert result2.get("type") is FlowResultType.CREATE_ENTRY
    assert result2.get("title") == "Spy cam"
    assert result2.get("data") == {}
    assert result2.get("options") == {
        CONF_AUTHENTICATION: HTTP_BASIC_AUTHENTICATION,
        CONF_MJPEG_URL: "https://example.com/mjpeg",
        CONF_PASSWORD: "omgpuppies",
        CONF_STILL_IMAGE_URL: "https://example.com/still",
        CONF_USERNAME: "frenck",
        CONF_VERIFY_SSL: False,
    }

    assert len(mock_setup_entry.mock_calls) == 1
    assert mock_mjpeg_requests.call_count == 2