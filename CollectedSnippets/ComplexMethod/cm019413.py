async def test_connection_error(
    hass: HomeAssistant,
    mock_mjpeg_requests: Mocker,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test connection error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "user"

    # Test connectione error on MJPEG url
    mock_mjpeg_requests.get(
        "https://example.com/mjpeg", exc=requests.exceptions.ConnectionError
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "My cam",
            CONF_MJPEG_URL: "https://example.com/mjpeg",
            CONF_STILL_IMAGE_URL: "https://example.com/still",
        },
    )

    assert result2.get("type") is FlowResultType.FORM
    assert result2.get("step_id") == "user"
    assert result2.get("errors") == {"mjpeg_url": "cannot_connect"}

    assert len(mock_setup_entry.mock_calls) == 0
    assert mock_mjpeg_requests.call_count == 1

    # Reset
    mock_mjpeg_requests.get("https://example.com/mjpeg", text="resp")

    # Test connectione error on still url
    mock_mjpeg_requests.get(
        "https://example.com/still", exc=requests.exceptions.ConnectionError
    )
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        user_input={
            CONF_NAME: "My cam",
            CONF_MJPEG_URL: "https://example.com/mjpeg",
            CONF_STILL_IMAGE_URL: "https://example.com/still",
        },
    )

    assert result3.get("type") is FlowResultType.FORM
    assert result3.get("step_id") == "user"
    assert result3.get("errors") == {"still_image_url": "cannot_connect"}

    assert len(mock_setup_entry.mock_calls) == 0
    assert mock_mjpeg_requests.call_count == 3

    # Reset
    mock_mjpeg_requests.get("https://example.com/still", text="resp")

    # Finish
    result4 = await hass.config_entries.flow.async_configure(
        result3["flow_id"],
        user_input={
            CONF_NAME: "My cam",
            CONF_MJPEG_URL: "https://example.com/mjpeg",
            CONF_STILL_IMAGE_URL: "https://example.com/still",
        },
    )

    assert result4.get("type") is FlowResultType.CREATE_ENTRY
    assert result4.get("title") == "My cam"
    assert result4.get("data") == {}
    assert result4.get("options") == {
        CONF_AUTHENTICATION: HTTP_BASIC_AUTHENTICATION,
        CONF_MJPEG_URL: "https://example.com/mjpeg",
        CONF_PASSWORD: "",
        CONF_STILL_IMAGE_URL: "https://example.com/still",
        CONF_USERNAME: None,
        CONF_VERIFY_SSL: True,
    }

    assert len(mock_setup_entry.mock_calls) == 1
    assert mock_mjpeg_requests.call_count == 5