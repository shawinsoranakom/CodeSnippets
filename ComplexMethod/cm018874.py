async def test_reauth(hass: HomeAssistant, requests_mock: Mocker) -> None:
    """Test we can reauth."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_USERNAME: "test@test.org",
            CONF_CLIENT_ID: "client_id",
            CONF_CLIENT_SECRET: "client_secret",
        },
        unique_id="test@test.org",
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_PASSWORD: "test-password",
        },
    )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {"password": "invalid_auth"}

    requests_mock.register_uri(
        "GET",
        DEVICE_LIST_URL,
        exc=requests.exceptions.ConnectTimeout,
    )

    with (
        patch(
            "homeassistant.components.flume.config_flow.os.path.exists",
            return_value=True,
        ),
        patch("homeassistant.components.flume.config_flow.os.unlink") as mock_unlink,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {
                CONF_PASSWORD: "test-password",
            },
        )
        # The existing token file was removed
        assert len(mock_unlink.mock_calls) == 1

    assert result3["type"] is FlowResultType.FORM
    assert result3["errors"] == {"base": "cannot_connect"}

    requests_mock.register_uri(
        "GET",
        DEVICE_LIST_URL,
        status_code=HTTPStatus.OK,
        json={
            "data": DEVICE_LIST,
        },
    )

    with (
        patch(
            "homeassistant.components.flume.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result4 = await hass.config_entries.flow.async_configure(
            result3["flow_id"],
            {
                CONF_PASSWORD: "test-password",
            },
        )

    assert mock_setup_entry.called
    assert result4["type"] is FlowResultType.ABORT
    assert result4["reason"] == "reauth_successful"