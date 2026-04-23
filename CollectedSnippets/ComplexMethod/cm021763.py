async def test_internal_discovery_callback_fill_out_cast_type_manufacturer(
    hass: HomeAssistant, get_cast_type_mock, caplog: pytest.LogCaptureFixture
) -> None:
    """Test internal discovery automatically filling out information."""
    discover_cast, _, _ = await async_setup_cast_internal_discovery(hass)
    info = get_fake_chromecast_info(
        host="host1",
        port=8009,
        service=FAKE_MDNS_SERVICE,
        cast_type=None,
        manufacturer=None,
    )
    info2 = get_fake_chromecast_info(
        host="host1",
        port=8009,
        service=FAKE_MDNS_SERVICE,
        cast_type=None,
        manufacturer=None,
        model_name="Model 101",
    )
    zconf = get_fake_zconf(host="host1", port=8009)
    full_info = attr.evolve(
        info,
        cast_info=pychromecast.discovery.CastInfo(
            services=info.cast_info.services,
            uuid=FakeUUID,
            model_name="Chromecast",
            friendly_name="Speaker",
            host=info.cast_info.host,
            port=info.cast_info.port,
            cast_type="audio",
            manufacturer="TrollTech",
        ),
        is_dynamic_group=None,
    )
    full_info2 = attr.evolve(
        info2,
        cast_info=pychromecast.discovery.CastInfo(
            services=info.cast_info.services,
            uuid=FakeUUID,
            model_name="Model 101",
            friendly_name="Speaker",
            host=info.cast_info.host,
            port=info.cast_info.port,
            cast_type="cast",
            manufacturer="Cyberdyne Systems",
        ),
        is_dynamic_group=None,
    )

    get_cast_type_mock.assert_not_called()
    get_cast_type_mock.return_value = full_info.cast_info

    with patch(
        "homeassistant.components.cast.discovery.ChromeCastZeroconf.get_zeroconf",
        return_value=zconf,
    ):
        signal = MagicMock()

        async_dispatcher_connect(hass, "cast_discovered", signal)
        discover_cast(FAKE_MDNS_SERVICE, info)
        await hass.async_block_till_done()

        # when called with incomplete info, it should use HTTP to get missing
        get_cast_type_mock.assert_called_once()
        assert get_cast_type_mock.call_count == 1
        discover = signal.mock_calls[2][1][0]
        assert discover == full_info
        assert "Fetched cast details for unknown model 'Chromecast'" in caplog.text

        signal.reset_mock()
        # Call again, the model name should be fetched from cache
        discover_cast(FAKE_MDNS_SERVICE, info)
        await hass.async_block_till_done()
        assert get_cast_type_mock.call_count == 1  # No additional calls
        discover = signal.mock_calls[0][1][0]
        assert discover == full_info

        signal.reset_mock()
        # Call for another model, need to call HTTP again
        get_cast_type_mock.return_value = full_info2.cast_info
        discover_cast(FAKE_MDNS_SERVICE, info2)
        await hass.async_block_till_done()
        assert get_cast_type_mock.call_count == 2
        discover = signal.mock_calls[0][1][0]
        assert discover == full_info2