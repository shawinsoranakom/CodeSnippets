async def test_send_video(
    hass: HomeAssistant,
    mock_broadcast_config_entry: MockConfigEntry,
    mock_external_calls: None,
) -> None:
    """Test answer callback query."""
    mock_broadcast_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_broadcast_config_entry.entry_id)
    await hass.async_block_till_done()

    # test: invalid file path

    with pytest.raises(ServiceValidationError) as err:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SEND_VIDEO,
            {
                ATTR_FILE: "/mock/file",
            },
            blocking=True,
        )

    await hass.async_block_till_done()

    assert err.value.translation_domain == DOMAIN
    assert err.value.translation_key == "allowlist_external_dirs_error"

    # test: missing username input

    with pytest.raises(ServiceValidationError) as err:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SEND_VIDEO,
            {
                ATTR_URL: "https://mock",
                ATTR_AUTHENTICATION: HTTP_DIGEST_AUTHENTICATION,
                ATTR_PASSWORD: "mock password",
            },
            blocking=True,
        )

    await hass.async_block_till_done()

    assert err.value.translation_domain == DOMAIN
    assert err.value.translation_key == "missing_input"
    assert err.value.translation_placeholders == {"field": "Username"}

    # test: missing password input

    with pytest.raises(ServiceValidationError) as err:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SEND_VIDEO,
            {
                ATTR_URL: "https://mock",
                ATTR_AUTHENTICATION: HTTP_BEARER_AUTHENTICATION,
            },
            blocking=True,
        )

    await hass.async_block_till_done()

    assert err.value.translation_domain == DOMAIN
    assert err.value.translation_key == "missing_input"
    assert err.value.translation_placeholders == {"field": "Password"}

    # test: 404 error

    with patch(
        "homeassistant.components.telegram_bot.bot.httpx.AsyncClient.get"
    ) as mock_get:
        mock_get.return_value = AsyncMock(status_code=404, text="Success")

        with pytest.raises(HomeAssistantError) as err:
            await hass.services.async_call(
                DOMAIN,
                SERVICE_SEND_VIDEO,
                {
                    ATTR_URL: "https://mock",
                    ATTR_AUTHENTICATION: HTTP_BASIC_AUTHENTICATION,
                    ATTR_USERNAME: "mock_bot",
                    ATTR_PASSWORD: "mock password",
                },
                blocking=True,
            )

    await hass.async_block_till_done()

    assert mock_get.call_count > 0
    assert err.value.translation_domain == DOMAIN
    assert err.value.translation_key == "failed_to_load_url"
    assert err.value.translation_placeholders == {"error": "404"}

    # test: invalid url

    with pytest.raises(HomeAssistantError) as err:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SEND_VIDEO,
            {
                ATTR_URL: "invalid url",
                ATTR_VERIFY_SSL: True,
                ATTR_AUTHENTICATION: HTTP_BEARER_AUTHENTICATION,
                ATTR_PASSWORD: "mock password",
            },
            blocking=True,
        )

    await hass.async_block_till_done()

    assert mock_get.call_count > 0
    assert err.value.translation_domain == DOMAIN
    assert err.value.translation_key == "failed_to_load_url"
    assert err.value.translation_placeholders == {
        "error": "Request URL is missing an 'http://' or 'https://' protocol."
    }

    # test: no url/file input

    with pytest.raises(ServiceValidationError) as err:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SEND_VIDEO,
            {},
            blocking=True,
        )

    await hass.async_block_till_done()

    assert err.value.translation_domain == DOMAIN
    assert err.value.translation_key == "missing_input"
    assert err.value.translation_placeholders == {"field": "URL or File"}

    # test: load file error (e.g. not found, permissions error)

    hass.config.allowlist_external_dirs.add("/tmp/")  # noqa: S108

    with pytest.raises(HomeAssistantError) as err:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SEND_VIDEO,
            {
                ATTR_FILE: "/tmp/not-exists",  # noqa: S108
            },
            blocking=True,
        )

    await hass.async_block_till_done()

    assert err.value.translation_domain == DOMAIN
    assert err.value.translation_key == "failed_to_load_file"
    assert err.value.translation_placeholders == {
        "error": "[Errno 2] No such file or directory: '/tmp/not-exists'"
    }

    # test: success with file
    write_utf8_file("/tmp/mock", "mock file contents")  # noqa: S108

    response = await hass.services.async_call(
        DOMAIN,
        SERVICE_SEND_VIDEO,
        {
            ATTR_FILE: "/tmp/mock",  # noqa: S108
        },
        blocking=True,
        return_response=True,
    )

    await hass.async_block_till_done()
    assert response == {
        "chats": [
            {
                ATTR_CHAT_ID: 123456,
                ATTR_MESSAGE_ID: 12345,
                ATTR_ENTITY_ID: "notify.mock_title_mock_chat_1",
            }
        ]
    }

    # test: success with url

    with patch(
        "homeassistant.components.telegram_bot.bot.httpx.AsyncClient.get"
    ) as mock_get:
        mock_get.return_value = AsyncMock(status_code=200, content=b"mock content")

        response = await hass.services.async_call(
            DOMAIN,
            SERVICE_SEND_VIDEO,
            {
                ATTR_URL: "https://mock",
                ATTR_AUTHENTICATION: HTTP_DIGEST_AUTHENTICATION,
                ATTR_USERNAME: "mock_bot",
                ATTR_PASSWORD: "mock password",
            },
            blocking=True,
            return_response=True,
        )

    await hass.async_block_till_done()
    assert mock_get.call_count > 0
    assert response == {
        "chats": [
            {
                ATTR_CHAT_ID: 123456,
                ATTR_MESSAGE_ID: 12345,
                ATTR_ENTITY_ID: "notify.mock_title_mock_chat_1",
            }
        ]
    }