async def test_options_flow(
    hass: HomeAssistant,
    mock_mjpeg_requests: Mocker,
    init_integration: MockConfigEntry,
) -> None:
    """Test options config flow."""
    result = await hass.config_entries.options.async_init(init_integration.entry_id)

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "init"

    # Register a second camera
    mock_mjpeg_requests.get("https://example.com/second_camera", text="resp")
    mock_second_config_entry = MockConfigEntry(
        title="Another Camera",
        domain=DOMAIN,
        data={},
        options={
            CONF_AUTHENTICATION: HTTP_BASIC_AUTHENTICATION,
            CONF_MJPEG_URL: "https://example.com/second_camera",
            CONF_PASSWORD: "",
            CONF_STILL_IMAGE_URL: None,
            CONF_USERNAME: None,
            CONF_VERIFY_SSL: True,
        },
    )
    mock_second_config_entry.add_to_hass(hass)

    # Try updating options to already existing secondary camera
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_MJPEG_URL: "https://example.com/second_camera",
        },
    )

    assert result2.get("type") is FlowResultType.FORM
    assert result2.get("step_id") == "init"
    assert result2.get("errors") == {"mjpeg_url": "already_configured"}

    assert mock_mjpeg_requests.call_count == 1

    # Test connectione error on MJPEG url
    mock_mjpeg_requests.get(
        "https://example.com/invalid_mjpeg", exc=requests.exceptions.ConnectionError
    )
    result3 = await hass.config_entries.options.async_configure(
        result2["flow_id"],
        user_input={
            CONF_MJPEG_URL: "https://example.com/invalid_mjpeg",
            CONF_STILL_IMAGE_URL: "https://example.com/still",
        },
    )

    assert result3.get("type") is FlowResultType.FORM
    assert result3.get("step_id") == "init"
    assert result3.get("errors") == {"mjpeg_url": "cannot_connect"}

    assert mock_mjpeg_requests.call_count == 2

    # Test connectione error on still url
    mock_mjpeg_requests.get(
        "https://example.com/invalid_still", exc=requests.exceptions.ConnectionError
    )
    result4 = await hass.config_entries.options.async_configure(
        result3["flow_id"],
        user_input={
            CONF_MJPEG_URL: "https://example.com/mjpeg",
            CONF_STILL_IMAGE_URL: "https://example.com/invalid_still",
        },
    )

    assert result4.get("type") is FlowResultType.FORM
    assert result4.get("step_id") == "init"
    assert result4.get("errors") == {"still_image_url": "cannot_connect"}

    assert mock_mjpeg_requests.call_count == 4

    # Invalid credentials
    mock_mjpeg_requests.get(
        "https://example.com/invalid_auth", text="Access Denied!", status_code=401
    )
    result5 = await hass.config_entries.options.async_configure(
        result4["flow_id"],
        user_input={
            CONF_MJPEG_URL: "https://example.com/invalid_auth",
            CONF_PASSWORD: "omgpuppies",
            CONF_USERNAME: "frenck",
        },
    )

    assert result5.get("type") is FlowResultType.FORM
    assert result5.get("step_id") == "init"
    assert result5.get("errors") == {"username": "invalid_auth"}

    assert mock_mjpeg_requests.call_count == 6

    # Finish
    result6 = await hass.config_entries.options.async_configure(
        result5["flow_id"],
        user_input={
            CONF_MJPEG_URL: "https://example.com/mjpeg",
            CONF_PASSWORD: "evenmorepuppies",
            CONF_USERNAME: "newuser",
        },
    )

    assert result6.get("type") is FlowResultType.CREATE_ENTRY
    assert result6.get("data") == {
        CONF_AUTHENTICATION: HTTP_BASIC_AUTHENTICATION,
        CONF_MJPEG_URL: "https://example.com/mjpeg",
        CONF_PASSWORD: "evenmorepuppies",
        CONF_STILL_IMAGE_URL: None,
        CONF_USERNAME: "newuser",
        CONF_VERIFY_SSL: True,
    }

    assert mock_mjpeg_requests.call_count == 7