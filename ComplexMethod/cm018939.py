async def test_setup_when_certificate_changed(
    hass: HomeAssistant,
    requests_mock: requests_mock.Mocker,
    empty_library,
    empty_payload,
    plex_server_accounts,
    plex_server_default,
    plextv_account,
    plextv_resources,
    plextv_shared_users,
    mock_websocket,
) -> None:
    """Test setup component when the Plex certificate has changed."""

    class WrongCertHostnameException(requests.exceptions.SSLError):
        """Mock the exception showing a mismatched hostname."""

        def __init__(self) -> None:  # pylint: disable=super-init-not-called
            self.__context__ = ssl.SSLCertVerificationError(
                f"hostname '{old_domain}' doesn't match"
            )

    old_domain = "1-2-3-4.1111111111ffffff1111111111ffffff.plex.direct"
    old_url = f"https://{old_domain}:32400"

    OLD_HOSTNAME_DATA = copy.deepcopy(DEFAULT_DATA)
    OLD_HOSTNAME_DATA[const.PLEX_SERVER_CONFIG][CONF_URL] = old_url

    old_entry = MockConfigEntry(
        domain=const.DOMAIN,
        data=OLD_HOSTNAME_DATA,
        options=DEFAULT_OPTIONS,
        unique_id=DEFAULT_DATA["server_id"],
    )

    requests_mock.get("https://plex.tv/api/users/", text=plextv_shared_users)
    requests_mock.get("https://plex.tv/api/invites/requested", text=empty_payload)
    requests_mock.get(old_url, exc=WrongCertHostnameException)

    # Test with account failure
    requests_mock.get(
        "https://plex.tv/api/v2/user", status_code=HTTPStatus.UNAUTHORIZED
    )
    old_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(old_entry.entry_id) is False
    await hass.async_block_till_done()

    assert old_entry.state is ConfigEntryState.SETUP_ERROR
    await hass.config_entries.async_unload(old_entry.entry_id)

    # Test with no servers found
    requests_mock.get("https://plex.tv/api/v2/user", text=plextv_account)
    requests_mock.get("https://plex.tv/api/v2/resources", text=empty_payload)

    assert await hass.config_entries.async_setup(old_entry.entry_id) is False
    await hass.async_block_till_done()

    assert old_entry.state is ConfigEntryState.SETUP_ERROR
    await hass.config_entries.async_unload(old_entry.entry_id)

    # Test with success
    new_url = PLEX_DIRECT_URL
    requests_mock.get("https://plex.tv/api/v2/resources", text=plextv_resources)
    for resource_url in (new_url, "http://1.2.3.4:32400"):
        requests_mock.get(resource_url, text=plex_server_default)
    requests_mock.get(f"{new_url}/accounts", text=plex_server_accounts)
    requests_mock.get(f"{new_url}/library", text=empty_library)
    requests_mock.get(f"{new_url}/library/sections", text=empty_payload)

    assert await hass.config_entries.async_setup(old_entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.config_entries.async_entries(const.DOMAIN)) == 1
    assert old_entry.state is ConfigEntryState.LOADED

    assert old_entry.data[const.PLEX_SERVER_CONFIG][CONF_URL] == new_url