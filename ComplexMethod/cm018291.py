async def test_load_image_from_url(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    hass_client: ClientSessionGenerator,
    freezer: FrozenDateTimeFactory,
    xbox_live_client: AsyncMock,
) -> None:
    """Test image platform loads image from url."""

    freezer.move_to("2025-06-16T00:00:00-00:00")

    respx.get(
        "https://images-eds-ssl.xboxlive.com/image?url=wHwbXKif8cus8csoZ03RW_ES.ojiJijNBGRVUbTnZKsoCCCkjlsEJrrMqDkYqs3M0aLOK2"
        "kxE9mbLm9M2.R0stAQYoDsGCDJxqDzG9WF3oa4rOCjEK7DbZXdBmBWnMrfErA3M_Q4y_mUTEQLqSAEeYFGlGeCXYsccnQMvEecxRg-&format=png"
    ).respond(status_code=HTTPStatus.OK, content_type="image/png", content=b"Test")
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED

    assert (state := hass.states.get("image.gsr_ae_gamerpic"))
    assert state.state == "2025-06-16T00:00:00+00:00"

    access_token = state.attributes["access_token"]
    assert (
        state.attributes["entity_picture"]
        == f"/api/image_proxy/image.gsr_ae_gamerpic?token={access_token}"
    )

    client = await hass_client()
    resp = await client.get(state.attributes["entity_picture"])
    assert resp.status == HTTPStatus.OK
    body = await resp.read()
    assert body == b"Test"
    assert resp.content_type == "image/png"
    assert resp.content_length == 4

    xbox_live_client.people.get_friend_by_xuid.return_value = PeopleResponse(
        **await async_load_json_object_fixture(
            hass, "people_batch gamerpic.json", DOMAIN
        )  # pyright: ignore[reportArgumentType]
    )

    respx.get(
        "https://images-eds-ssl.xboxlive.com/image?url=KT_QTPJeC5ZpnbX.xahcbrZ9enA_IV9WfFEWIqHGUb5P30TpCdy9xIzUMuqZVCfbWmxtVC"
        "rgWHJigthrlsHCxEOMG9UGNdojCYasYt6MJHBjmxmtuAHJeo.sOkUiPmg4JHXvOS82c3UOrvdJTDaCKwCwHPJ0t0Plha8oHFC1i_o-&format=png"
    ).respond(status_code=HTTPStatus.OK, content_type="image/png", content=b"Test2")

    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert (state := hass.states.get("image.gsr_ae_gamerpic"))
    assert state.state == "2025-06-16T00:00:30+00:00"

    access_token = state.attributes["access_token"]
    assert (
        state.attributes["entity_picture"]
        == f"/api/image_proxy/image.gsr_ae_gamerpic?token={access_token}"
    )

    client = await hass_client()
    resp = await client.get(state.attributes["entity_picture"])
    assert resp.status == HTTPStatus.OK
    body = await resp.read()
    assert body == b"Test2"
    assert resp.content_type == "image/png"
    assert resp.content_length == 5