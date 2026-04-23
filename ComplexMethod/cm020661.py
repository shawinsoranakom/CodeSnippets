async def test_reconfigure_cleans_up_device(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    get_client: NordPoolClient,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test clean up devices due to reconfiguration."""
    nl_json_file = await async_load_fixture(hass, "delivery_period_nl.json", DOMAIN)
    load_nl_json = json.loads(nl_json_file)

    entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        data=ENTRY_CONFIG,
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert entry.state is ConfigEntryState.LOADED

    assert device_registry.async_get_device(identifiers={(DOMAIN, "SE3")})
    assert device_registry.async_get_device(identifiers={(DOMAIN, "SE4")})
    assert entity_registry.async_get("sensor.nord_pool_se3_current_price")
    assert entity_registry.async_get("sensor.nord_pool_se4_current_price")
    assert hass.states.get("sensor.nord_pool_se3_current_price")
    assert hass.states.get("sensor.nord_pool_se4_current_price")

    aioclient_mock.clear_requests()
    aioclient_mock.request(
        "GET",
        url=API + "/DayAheadPrices",
        params={
            "date": "2025-09-30",
            "market": "DayAhead",
            "deliveryArea": "NL",
            "currency": "EUR",
        },
        json=load_nl_json,
    )
    aioclient_mock.request(
        "GET",
        url=API + "/DayAheadPrices",
        params={
            "date": "2025-10-01",
            "market": "DayAhead",
            "deliveryArea": "NL",
            "currency": "EUR",
        },
        json=load_nl_json,
    )
    aioclient_mock.request(
        "GET",
        url=API + "/DayAheadPrices",
        params={
            "date": "2025-10-02",
            "market": "DayAhead",
            "deliveryArea": "NL",
            "currency": "EUR",
        },
        json=load_nl_json,
    )

    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_AREAS: ["NL"],
            CONF_CURRENCY: "EUR",
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data == {
        "areas": [
            "NL",
        ],
        "currency": "EUR",
    }
    await hass.async_block_till_done(wait_background_tasks=True)

    assert device_registry.async_get_device(identifiers={(DOMAIN, "NL")})
    assert entity_registry.async_get("sensor.nord_pool_nl_current_price")
    assert hass.states.get("sensor.nord_pool_nl_current_price")

    assert not device_registry.async_get_device(identifiers={(DOMAIN, "SE3")})
    assert not entity_registry.async_get("sensor.nord_pool_se3_current_price")
    assert not hass.states.get("sensor.nord_pool_se3_current_price")
    assert not device_registry.async_get_device(identifiers={(DOMAIN, "SE4")})
    assert not entity_registry.async_get("sensor.nord_pool_se4_current_price")
    assert not hass.states.get("sensor.nord_pool_se4_current_price")