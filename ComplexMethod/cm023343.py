async def test_event_notifier(
    hass: HomeAssistant, aiohttp_notify_servers_mock: Mock
) -> None:
    """Test getting and releasing event notifiers."""
    domain_data = get_domain_data(hass)

    listen_addr = EventListenAddr(None, 0, None)
    event_notifier = await domain_data.async_get_event_notifier(listen_addr, hass)
    assert event_notifier is not None

    # Check that the parameters were passed through to the AiohttpNotifyServer
    aiohttp_notify_servers_mock.assert_called_with(
        requester=ANY, source=("0.0.0.0", 0), callback_url=None, loop=ANY
    )

    # Same address should give same notifier
    listen_addr_2 = EventListenAddr(None, 0, None)
    event_notifier_2 = await domain_data.async_get_event_notifier(listen_addr_2, hass)
    assert event_notifier_2 is event_notifier

    # Different address should give different notifier
    listen_addr_3 = EventListenAddr(
        "198.51.100.4", 9999, "http://198.51.100.4:9999/notify"
    )
    event_notifier_3 = await domain_data.async_get_event_notifier(listen_addr_3, hass)
    assert event_notifier_3 is not None
    assert event_notifier_3 is not event_notifier

    # Check that the parameters were passed through to the AiohttpNotifyServer
    aiohttp_notify_servers_mock.assert_called_with(
        requester=ANY,
        source=("198.51.100.4", 9999),
        callback_url="http://198.51.100.4:9999/notify",
        loop=ANY,
    )

    # There should be 2 notifiers total, one with 2 references, and a stop callback
    assert set(domain_data.event_notifiers.keys()) == {listen_addr, listen_addr_3}
    assert domain_data.event_notifier_refs == {listen_addr: 2, listen_addr_3: 1}
    assert domain_data.stop_listener_remove is not None

    # Releasing notifiers should delete them when they have not more references
    await domain_data.async_release_event_notifier(listen_addr)
    assert set(domain_data.event_notifiers.keys()) == {listen_addr, listen_addr_3}
    assert domain_data.event_notifier_refs == {listen_addr: 1, listen_addr_3: 1}
    assert domain_data.stop_listener_remove is not None

    await domain_data.async_release_event_notifier(listen_addr)
    assert set(domain_data.event_notifiers.keys()) == {listen_addr_3}
    assert domain_data.event_notifier_refs == {listen_addr: 0, listen_addr_3: 1}
    assert domain_data.stop_listener_remove is not None

    await domain_data.async_release_event_notifier(listen_addr_3)
    assert set(domain_data.event_notifiers.keys()) == set()
    assert domain_data.event_notifier_refs == {listen_addr: 0, listen_addr_3: 0}
    assert domain_data.stop_listener_remove is None