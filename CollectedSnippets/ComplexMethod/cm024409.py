async def test_alerts_change(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    aioclient_mock: AiohttpClientMocker,
    ha_version: str,
    fixture_1: str,
    expected_alerts_1: list[tuple[str, str]],
    fixture_2: str,
    expected_alerts_2: list[tuple[str, str]],
) -> None:
    """Test creating issues based on alerts."""
    fixture_1_content = await async_load_fixture(hass, fixture_1, DOMAIN)
    aioclient_mock.clear_requests()
    aioclient_mock.get(
        "https://alerts.home-assistant.io/alerts.json",
        text=fixture_1_content,
    )
    for alert in json.loads(fixture_1_content):
        stub_alert(aioclient_mock, alert["id"])

    activated_components = (
        "aladdin_connect",
        "darksky",
        "hikvision",
        "hikvisioncam",
        "hive",
        "homematicip_cloud",
        "logi_circle",
        "neato",
        "nest",
        "senseme",
        "sochain",
    )
    for domain in activated_components:
        hass.config.components.add(domain)

    with patch(
        "homeassistant.components.homeassistant_alerts.coordinator.__version__",
        ha_version,
    ):
        assert await async_setup_component(hass, DOMAIN, {})

    now = dt_util.utcnow()

    client = await hass_ws_client(hass)

    await client.send_json({"id": 1, "type": "repairs/list_issues"})
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"]["issues"] == unordered(
        [
            {
                "breaks_in_ha_version": None,
                "created": ANY,
                "dismissed_version": None,
                "domain": DOMAIN,
                "ignored": False,
                "is_fixable": False,
                "issue_id": f"{alert_id}.markdown_{integration}",
                "issue_domain": integration,
                "learn_more_url": None,
                "severity": "warning",
                "translation_key": "alert",
                "translation_placeholders": {
                    "title": f"Title for {alert_id}",
                    "description": f"Content for {alert_id}",
                },
            }
            for alert_id, integration in expected_alerts_1
        ]
    )

    fixture_2_content = await async_load_fixture(hass, fixture_2, DOMAIN)
    aioclient_mock.clear_requests()
    aioclient_mock.get(
        "https://alerts.home-assistant.io/alerts.json",
        text=fixture_2_content,
    )
    for alert in json.loads(fixture_2_content):
        stub_alert(aioclient_mock, alert["id"])

    future = now + UPDATE_INTERVAL + timedelta(seconds=1)
    async_fire_time_changed(hass, future)
    await hass.async_block_till_done()

    await client.send_json({"id": 2, "type": "repairs/list_issues"})
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"]["issues"] == unordered(
        [
            {
                "breaks_in_ha_version": None,
                "created": ANY,
                "dismissed_version": None,
                "domain": DOMAIN,
                "ignored": False,
                "is_fixable": False,
                "issue_id": f"{alert_id}.markdown_{integration}",
                "issue_domain": integration,
                "learn_more_url": None,
                "severity": "warning",
                "translation_key": "alert",
                "translation_placeholders": {
                    "title": f"Title for {alert_id}",
                    "description": f"Content for {alert_id}",
                },
            }
            for alert_id, integration in expected_alerts_2
        ]
    )