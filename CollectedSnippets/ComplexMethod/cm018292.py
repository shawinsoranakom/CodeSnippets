async def test_browse_media(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    snapshot: SnapshotAssertion,
) -> None:
    """Test browsing media."""

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED

    assert (
        await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}")
    ).as_dict() == snapshot(name="games_view")

    assert (
        await async_browse_media(
            hass, f"{URI_SCHEME}{DOMAIN}/271958441785640/1297287135"
        )
    ).as_dict() == snapshot(name="category_view")

    assert (
        await async_browse_media(
            hass, f"{URI_SCHEME}{DOMAIN}/271958441785640/1297287135/gameclips"
        )
    ).as_dict() == snapshot(name="gameclips_view")

    assert (
        await async_browse_media(
            hass, f"{URI_SCHEME}{DOMAIN}/271958441785640/1297287135/screenshots"
        )
    ).as_dict() == snapshot(name="screenshots_view")

    assert (
        await async_browse_media(
            hass, f"{URI_SCHEME}{DOMAIN}/271958441785640/1297287135/game_media"
        )
    ).as_dict() == snapshot(name="game_media_view")

    assert (
        await async_browse_media(
            hass, f"{URI_SCHEME}{DOMAIN}/271958441785640/1297287135/community_gameclips"
        )
    ).as_dict() == snapshot(name="community_gameclips_view")

    assert (
        await async_browse_media(
            hass,
            f"{URI_SCHEME}{DOMAIN}/271958441785640/1297287135/community_screenshots",
        )
    ).as_dict() == snapshot(name="community_screenshots_view")