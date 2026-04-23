async def test_image_platform(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    snapshot: SnapshotAssertion,
    hass_client: ClientSessionGenerator,
    habitica: AsyncMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test image platform."""
    freezer.move_to("2024-09-20T22:00:00.000")
    with patch(
        "homeassistant.components.habitica.coordinator.BytesIO",
    ) as avatar:
        avatar.side_effect = [
            BytesIO(b"\x89PNGTestImage1"),
            BytesIO(b"\x89PNGTestImage2"),
        ]

        config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        assert config_entry.state is ConfigEntryState.LOADED

        assert (state := hass.states.get("image.test_user_avatar"))
        assert state.state == "2024-09-20T22:00:00+00:00"

        access_token = state.attributes["access_token"]
        assert (
            state.attributes["entity_picture"]
            == f"/api/image_proxy/image.test_user_avatar?token={access_token}"
        )

        client = await hass_client()
        resp = await client.get(state.attributes["entity_picture"])
        assert resp.status == HTTPStatus.OK

        assert (await resp.read()) == b"\x89PNGTestImage1"

        habitica.get_user.return_value = HabiticaUserResponse.from_json(
            await async_load_fixture(hass, "rogue_fixture.json", DOMAIN)
        )

        freezer.tick(timedelta(seconds=60))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

        assert (state := hass.states.get("image.test_user_avatar"))
        assert state.state == "2024-09-20T22:01:00+00:00"

        resp = await client.get(state.attributes["entity_picture"])
        assert resp.status == HTTPStatus.OK

        assert (await resp.read()) == b"\x89PNGTestImage2"