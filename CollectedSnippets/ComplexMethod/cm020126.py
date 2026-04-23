async def test_setup_api_push_api_data_default(
    hass: HomeAssistant, hass_storage: dict[str, Any], supervisor_client: AsyncMock
) -> None:
    """Test setup with API push default data."""
    with (
        patch.dict(os.environ, MOCK_ENVIRON),
        patch("homeassistant.components.hassio.config.STORE_DELAY_SAVE", 0),
    ):
        result = await async_setup_component(hass, "hassio", {"http": {}, "hassio": {}})
        await hass.async_block_till_done()

    assert result
    assert len(supervisor_client.mock_calls) == 25
    supervisor_client.homeassistant.set_options.assert_called_once_with(
        HomeAssistantOptions(ssl=False, port=8123, refresh_token=ANY)
    )
    refresh_token = (
        supervisor_client.homeassistant.set_options.mock_calls[0].args[0].refresh_token
    )
    hassio_user = await hass.auth.async_get_user(
        hass_storage[STORAGE_KEY]["data"]["hassio_user"]
    )
    assert hassio_user is not None
    assert hassio_user.system_generated
    assert len(hassio_user.groups) == 1
    assert hassio_user.groups[0].id == GROUP_ID_ADMIN
    assert hassio_user.name == "Supervisor"
    for token in hassio_user.refresh_tokens.values():
        if token.token == refresh_token:
            break
    else:
        pytest.fail("refresh token not found")