async def test_discover_dynamic_group(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    get_multizone_status_mock,
    get_chromecast_mock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test dynamic group does not create device or entity."""
    cast_1 = get_fake_chromecast_info(host="host_1", port=23456, uuid=FakeUUID)
    cast_2 = get_fake_chromecast_info(host="host_2", port=34567, uuid=FakeUUID2)
    zconf_1 = get_fake_zconf(host="host_1", port=23456)
    zconf_2 = get_fake_zconf(host="host_2", port=34567)

    # Fake dynamic group info
    tmp1 = MagicMock()
    tmp1.uuid = FakeUUID
    tmp2 = MagicMock()
    tmp2.uuid = FakeUUID2
    get_multizone_status_mock.return_value.dynamic_groups = [tmp1, tmp2]

    get_chromecast_mock.assert_not_called()
    discover_cast, remove_cast, add_dev1 = await async_setup_cast_internal_discovery(
        hass
    )

    tasks = []
    real_create_task = asyncio.create_task

    def create_task(coroutine, name):
        tasks.append(real_create_task(coroutine))

    # Discover cast service
    with (
        patch(
            "homeassistant.components.cast.discovery.ChromeCastZeroconf.get_zeroconf",
            return_value=zconf_1,
        ),
        patch.object(
            hass,
            "async_create_background_task",
            wraps=create_task,
        ),
    ):
        discover_cast(
            pychromecast.discovery.MDNSServiceInfo("service"),
            cast_1,
        )
        await hass.async_block_till_done()
        await hass.async_block_till_done()  # having tasks that add jobs

    assert len(tasks) == 1
    await asyncio.gather(*tasks)
    tasks.clear()
    get_chromecast_mock.assert_called()
    get_chromecast_mock.reset_mock()
    assert add_dev1.call_count == 0
    assert (
        entity_registry.async_get_entity_id("media_player", "cast", cast_1.uuid) is None
    )

    # Discover other dynamic group cast service
    with (
        patch(
            "homeassistant.components.cast.discovery.ChromeCastZeroconf.get_zeroconf",
            return_value=zconf_2,
        ),
        patch.object(
            hass,
            "async_create_background_task",
            wraps=create_task,
        ),
    ):
        discover_cast(
            pychromecast.discovery.MDNSServiceInfo("service"),
            cast_2,
        )
        await hass.async_block_till_done()
        await hass.async_block_till_done()  # having tasks that add jobs

    assert len(tasks) == 1
    await asyncio.gather(*tasks)
    tasks.clear()
    get_chromecast_mock.assert_called()
    get_chromecast_mock.reset_mock()
    assert add_dev1.call_count == 0
    assert (
        entity_registry.async_get_entity_id("media_player", "cast", cast_2.uuid) is None
    )

    # Get update for cast service
    with (
        patch(
            "homeassistant.components.cast.discovery.ChromeCastZeroconf.get_zeroconf",
            return_value=zconf_1,
        ),
        patch.object(
            hass,
            "async_create_background_task",
            wraps=create_task,
        ),
    ):
        discover_cast(
            pychromecast.discovery.MDNSServiceInfo("service"),
            cast_1,
        )
        await hass.async_block_till_done()
        await hass.async_block_till_done()  # having tasks that add jobs

    assert len(tasks) == 0
    get_chromecast_mock.assert_not_called()
    assert add_dev1.call_count == 0
    assert (
        entity_registry.async_get_entity_id("media_player", "cast", cast_1.uuid) is None
    )

    # Remove cast service
    assert "Disconnecting from chromecast" not in caplog.text

    with patch(
        "homeassistant.components.cast.discovery.ChromeCastZeroconf.get_zeroconf",
        return_value=zconf_1,
    ):
        remove_cast(
            pychromecast.discovery.MDNSServiceInfo("service"),
            cast_1,
        )
        await hass.async_block_till_done()
        await hass.async_block_till_done()  # having tasks that add jobs

    assert "Disconnecting from chromecast" in caplog.text