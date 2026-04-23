async def test_reauth(
    hass: HomeAssistant,
    login_requests_mock,
    login_response_text,
    expected_result,
    expected_entry_data,
) -> None:
    """Test reauth."""
    mock_entry_data = {**FIXTURE_USER_INPUT, CONF_PASSWORD: "invalid-password"}
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=FIXTURE_UNIQUE_ID,
        data=mock_entry_data,
        title="Reauth canary",
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["data_schema"] is not None
    assert result["data_schema"]({}) == {
        CONF_USERNAME: mock_entry_data[CONF_USERNAME],
        CONF_PASSWORD: mock_entry_data[CONF_PASSWORD],
    }
    assert not result["errors"]

    login_requests_mock.request(
        ANY,
        f"{FIXTURE_USER_INPUT[CONF_URL]}api/user/login",
        text=login_response_text,
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: FIXTURE_USER_INPUT[CONF_USERNAME],
            CONF_PASSWORD: FIXTURE_USER_INPUT[CONF_PASSWORD],
        },
    )
    await hass.async_block_till_done()

    for k, v in expected_result.items():
        assert result[k] == v  # type: ignore[literal-required] # expected is a subset
    for k, v in expected_entry_data.items():
        assert entry.data[k] == v