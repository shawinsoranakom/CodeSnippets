async def test_full_flow_with_authentication_error(
    hass: HomeAssistant,
    mock_mjpeg_requests: Mocker,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test the full user configuration flow with invalid credentials.

    This tests tests a full config flow, with a case the user enters an invalid
    credentials, but recovers by entering the correct ones.
    """
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "user"

    mock_mjpeg_requests.get(
        "https://example.com/mjpeg", text="Access Denied!", status_code=401
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Sky cam",
            CONF_MJPEG_URL: "https://example.com/mjpeg",
            CONF_PASSWORD: "omgpuppies",
            CONF_USERNAME: "frenck",
        },
    )

    assert result2.get("type") is FlowResultType.FORM
    assert result2.get("step_id") == "user"
    assert result2.get("errors") == {"username": "invalid_auth"}

    assert len(mock_setup_entry.mock_calls) == 0
    assert mock_mjpeg_requests.call_count == 2

    mock_mjpeg_requests.get("https://example.com/mjpeg", text="resp")
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        user_input={
            CONF_NAME: "Sky cam",
            CONF_MJPEG_URL: "https://example.com/mjpeg",
            CONF_PASSWORD: "supersecret",
            CONF_USERNAME: "frenck",
        },
    )

    assert result3.get("type") is FlowResultType.CREATE_ENTRY
    assert result3.get("title") == "Sky cam"
    assert result3.get("data") == {}
    assert result3.get("options") == {
        CONF_AUTHENTICATION: HTTP_BASIC_AUTHENTICATION,
        CONF_MJPEG_URL: "https://example.com/mjpeg",
        CONF_PASSWORD: "supersecret",
        CONF_STILL_IMAGE_URL: None,
        CONF_USERNAME: "frenck",
        CONF_VERIFY_SSL: True,
    }

    assert len(mock_setup_entry.mock_calls) == 1
    assert mock_mjpeg_requests.call_count == 3