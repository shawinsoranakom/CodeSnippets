async def test_rest_command_headers(
    hass: HomeAssistant,
    setup_component: ComponentSetup,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Call a rest command with custom headers and content types."""
    header_config_variations = {
        "no_headers_test": {},
        "content_type_test": {"content_type": CONTENT_TYPE_TEXT_PLAIN},
        "headers_test": {
            "headers": {
                "Accept": CONTENT_TYPE_JSON,
                "User-Agent": "Mozilla/5.0",
            }
        },
        "headers_and_content_type_test": {
            "headers": {"Accept": CONTENT_TYPE_JSON},
            "content_type": CONTENT_TYPE_TEXT_PLAIN,
        },
        "headers_and_content_type_override_test": {
            "headers": {
                "Accept": CONTENT_TYPE_JSON,
                aiohttp.hdrs.CONTENT_TYPE: "application/pdf",
            },
            "content_type": CONTENT_TYPE_TEXT_PLAIN,
        },
        "headers_template_test": {
            "headers": {
                "Accept": CONTENT_TYPE_JSON,
                "User-Agent": "Mozilla/{{ 3 + 2 }}.0",
            }
        },
        "headers_and_content_type_override_template_test": {
            "headers": {
                "Accept": "application/{{ 1 + 1 }}json",
                aiohttp.hdrs.CONTENT_TYPE: "application/pdf",
            },
            "content_type": "text/json",
        },
    }

    # add common parameters
    for variation in header_config_variations.values():
        variation.update({"url": TEST_URL, "method": "post", "payload": "test data"})

    await setup_component(header_config_variations)

    # provide post request data
    aioclient_mock.post(TEST_URL, content=b"success")

    for test_service in (
        "no_headers_test",
        "content_type_test",
        "headers_test",
        "headers_and_content_type_test",
        "headers_and_content_type_override_test",
        "headers_template_test",
        "headers_and_content_type_override_template_test",
    ):
        await hass.services.async_call(DOMAIN, test_service, {}, blocking=True)

    await hass.async_block_till_done()
    assert len(aioclient_mock.mock_calls) == 7

    # no_headers_test
    assert aioclient_mock.mock_calls[0][3] is None

    # content_type_test
    assert len(aioclient_mock.mock_calls[1][3]) == 1
    assert (
        aioclient_mock.mock_calls[1][3].get(aiohttp.hdrs.CONTENT_TYPE)
        == CONTENT_TYPE_TEXT_PLAIN
    )

    # headers_test
    assert len(aioclient_mock.mock_calls[2][3]) == 2
    assert aioclient_mock.mock_calls[2][3].get("Accept") == CONTENT_TYPE_JSON
    assert aioclient_mock.mock_calls[2][3].get("User-Agent") == "Mozilla/5.0"

    # headers_and_content_type_test
    assert len(aioclient_mock.mock_calls[3][3]) == 2
    assert (
        aioclient_mock.mock_calls[3][3].get(aiohttp.hdrs.CONTENT_TYPE)
        == CONTENT_TYPE_TEXT_PLAIN
    )
    assert aioclient_mock.mock_calls[3][3].get("Accept") == CONTENT_TYPE_JSON

    # headers_and_content_type_override_test
    assert len(aioclient_mock.mock_calls[4][3]) == 2
    assert (
        aioclient_mock.mock_calls[4][3].get(aiohttp.hdrs.CONTENT_TYPE)
        == CONTENT_TYPE_TEXT_PLAIN
    )
    assert aioclient_mock.mock_calls[4][3].get("Accept") == CONTENT_TYPE_JSON

    # headers_template_test
    assert len(aioclient_mock.mock_calls[5][3]) == 2
    assert aioclient_mock.mock_calls[5][3].get("Accept") == CONTENT_TYPE_JSON
    assert aioclient_mock.mock_calls[5][3].get("User-Agent") == "Mozilla/5.0"

    # headers_and_content_type_override_template_test
    assert len(aioclient_mock.mock_calls[6][3]) == 2
    assert aioclient_mock.mock_calls[6][3].get(aiohttp.hdrs.CONTENT_TYPE) == "text/json"
    assert aioclient_mock.mock_calls[6][3].get("Accept") == "application/2json"