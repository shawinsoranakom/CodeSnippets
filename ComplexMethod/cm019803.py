async def test_load_image_from_url(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    habitica: AsyncMock,
    hass_client: ClientSessionGenerator,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test loading of image from URL."""
    freezer.move_to("2024-09-20T22:00:00.000")

    call1 = respx.get(f"{ASSETS_URL}quest_atom1.png").respond(content=b"\x89PNG")
    call2 = respx.get(f"{ASSETS_URL}quest_dustbunnies.png").respond(content=b"\x89PNG")

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED

    assert (state := hass.states.get("image.test_user_s_party_quest"))
    assert state.state == "2024-09-20T22:00:00+00:00"

    client = await hass_client()
    resp = await client.get(state.attributes["entity_picture"])

    assert resp.status == HTTPStatus.OK

    assert (await resp.read()) == b"\x89PNG"

    assert call1.call_count == 1

    habitica.get_group.return_value = HabiticaGroupsResponse.from_json(
        await async_load_fixture(hass, "party_2.json", DOMAIN)
    )
    freezer.tick(timedelta(minutes=15))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert (state := hass.states.get("image.test_user_s_party_quest"))
    assert state.state == "2024-09-20T22:15:00+00:00"

    client = await hass_client()
    resp = await client.get(state.attributes["entity_picture"])

    assert resp.status == HTTPStatus.OK

    assert (await resp.read()) == b"\x89PNG"
    assert call2.call_count == 1