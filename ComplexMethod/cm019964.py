async def setup_evohome(
    hass: HomeAssistant,
    config: dict[str, str],
    install: str = "default",
) -> AsyncGenerator[MagicMock]:
    """Set up the evohome integration and return its client.

    The class is mocked here to check the client was instantiated with the correct args.
    """

    # set the time zone as for the active evohome location
    loc_idx: int = config.get("location_idx", 0)  # type: ignore[assignment]

    try:
        locn = user_locations_config_fixture(install)[loc_idx]
    except IndexError:
        if loc_idx == 0:
            raise
        locn = user_locations_config_fixture(install)[0]

    utc_offset: int = locn["locationInfo"]["timeZone"]["currentOffsetMinutes"]  # type: ignore[assignment, call-overload, index]
    dt_util.set_default_time_zone(timezone(timedelta(minutes=utc_offset)))

    with (
        # patch("homeassistant.components.evohome.ec1.EvohomeClient", return_value=None),
        patch("homeassistant.components.evohome.ec2.EvohomeClient") as mock_client,
        patch(
            "evohomeasync2.auth.CredentialsManagerBase._post_request",
            mock_post_request(install),
        ),
        patch("_evohome.auth.AbstractAuth._make_request", mock_make_request(install)),
    ):
        evo: EvohomeClient | None = None

        def evohome_client(*args, **kwargs) -> EvohomeClient:
            nonlocal evo
            evo = EvohomeClient(*args, **kwargs)
            return evo

        mock_client.side_effect = evohome_client

        assert await async_setup_component(hass, DOMAIN, {DOMAIN: config})
        await hass.async_block_till_done()

        mock_client.assert_called_once()

        assert isinstance(evo, EvohomeClient)
        assert evo._token_manager.client_id == config[CONF_USERNAME]
        assert evo._token_manager._secret == config[CONF_PASSWORD]

        assert evo.user_account

        mock_client.return_value = evo
        yield mock_client