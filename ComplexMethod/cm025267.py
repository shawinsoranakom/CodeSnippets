async def async_migrate_entry(hass: HomeAssistant, entry: XboxConfigEntry) -> bool:
    """Migrate config entry."""

    if entry.version == 1 and entry.minor_version < 3:
        try:
            implementation = await async_get_config_entry_implementation(hass, entry)
        except ImplementationUnavailableError as e:
            raise ConfigEntryNotReady(
                translation_domain=DOMAIN,
                translation_key="oauth2_implementation_unavailable",
            ) from e
        session = OAuth2Session(hass, entry, implementation)
        async_session = get_async_client(hass)
        auth = AsyncConfigEntryAuth(async_session, session)
        await auth.refresh_tokens()
        client = XboxLiveClient(auth)

        if entry.minor_version < 2:
            # Migrate unique_id from `xbox` to account xuid and
            # change generic entry name to user's gamertag
            try:
                own = await client.people.get_friend_by_xuid(client.xuid)
            except TimeoutException as e:
                raise ConfigEntryNotReady(
                    translation_domain=DOMAIN,
                    translation_key="timeout_exception",
                ) from e
            except (RequestError, HTTPStatusError) as e:
                _LOGGER.debug("Xbox exception:", exc_info=True)
                raise ConfigEntryNotReady(
                    translation_domain=DOMAIN,
                    translation_key="request_exception",
                ) from e

            hass.config_entries.async_update_entry(
                entry,
                unique_id=client.xuid,
                title=(
                    own.people[0].gamertag
                    if entry.title == "Home Assistant Cloud"
                    else entry.title
                ),
                minor_version=2,
            )
        if entry.minor_version < 3:
            # Migrate favorite friends to friend subentries
            try:
                friends = await client.people.get_friends_own()
            except TimeoutException as e:
                raise ConfigEntryNotReady(
                    translation_domain=DOMAIN,
                    translation_key="timeout_exception",
                ) from e
            except (RequestError, HTTPStatusError) as e:
                _LOGGER.debug("Xbox exception:", exc_info=True)
                raise ConfigEntryNotReady(
                    translation_domain=DOMAIN,
                    translation_key="request_exception",
                ) from e

            dev_reg = dr.async_get(hass)
            for friend in friends.people:
                if not friend.is_favorite:
                    continue
                subentry = ConfigSubentry(
                    subentry_type="friend",
                    title=friend.gamertag,
                    unique_id=friend.xuid,
                    data={},  # type: ignore[arg-type]
                )
                hass.config_entries.async_add_subentry(entry, subentry)

                if device := dev_reg.async_get_device({(DOMAIN, friend.xuid)}):
                    dev_reg.async_update_device(
                        device.id,
                        remove_config_entry_id=entry.entry_id,
                        add_config_subentry_id=subentry.subentry_id,
                        add_config_entry_id=entry.entry_id,
                    )
            if device := dev_reg.async_get_device({(DOMAIN, "xbox_live")}):
                dev_reg.async_update_device(
                    device.id, new_identifiers={(DOMAIN, client.xuid)}
                )
            hass.config_entries.async_update_entry(entry, minor_version=3)
            hass.config_entries.async_schedule_reload(entry.entry_id)
    return True