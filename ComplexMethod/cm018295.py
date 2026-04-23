async def test_unique_id_and_friends_migration(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test config entry unique_id migration and favorite to subentry migration."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Home Assistant Cloud",
        data={
            "auth_implementation": "cloud",
            "token": {
                "access_token": "1234567890",
                "expires_at": 1760697327.7298331,
                "expires_in": 3600,
                "refresh_token": "0987654321",
                "scope": "XboxLive.signin XboxLive.offline_access",
                "service": "xbox",
                "token_type": "bearer",
                "user_id": "AAAAAAAAAAAAAAAAAAAAA",
            },
        },
        unique_id=DOMAIN,
        version=1,
        minor_version=1,
    )

    config_entry.add_to_hass(hass)

    device_own = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, "xbox_live")},
    )

    device_friend = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, "2533274838782903")},
    )
    assert device_friend.config_entries_subentries[config_entry.entry_id] == {None}

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is config_entries.ConfigEntryState.LOADED
    assert config_entry.version == 1
    assert config_entry.minor_version == 3
    assert config_entry.unique_id == "271958441785640"
    assert config_entry.title == "GSR Ae"

    # Assert favorite friends migrated to subentries
    assert len(config_entry.subentries) == 1
    subentries = list(config_entry.subentries.values())
    assert subentries[0].unique_id == "2533274838782903"
    assert subentries[0].title == "Ikken Hissatsuu"
    assert subentries[0].subentry_type == "friend"

    ## Assert devices have been migrated
    assert (device_own := device_registry.async_get(device_own.id))
    assert device_own.identifiers == {(DOMAIN, "271958441785640")}

    assert (device_friend := device_registry.async_get(device_friend.id))
    assert device_friend.config_entries_subentries[config_entry.entry_id] == {
        subentries[0].subentry_id
    }