async def test_alerts_refreshed_on_component_load(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    aioclient_mock: AiohttpClientMocker,
    ha_version: str,
    supervisor_info: dict[str, str] | None,
    initial_components: list[str],
    late_components: list[str],
    initial_alerts: list[tuple[str, str]],
    late_alerts: list[tuple[str, str]],
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test alerts are refreshed when components are loaded."""

    aioclient_mock.clear_requests()
    aioclient_mock.get(
        "https://alerts.home-assistant.io/alerts.json",
        text=await async_load_fixture(hass, "alerts_1.json", DOMAIN),
    )
    for alert in initial_alerts:
        stub_alert(aioclient_mock, alert[0])
    for alert in late_alerts:
        stub_alert(aioclient_mock, alert[0])

    for domain in initial_components:
        hass.config.components.add(domain)

    with (
        patch(
            "homeassistant.components.homeassistant_alerts.coordinator.__version__",
            ha_version,
        ),
        patch(
            "homeassistant.components.homeassistant_alerts.coordinator.is_hassio",
            return_value=supervisor_info is not None,
        ),
        patch(
            "homeassistant.components.homeassistant_alerts.coordinator.get_supervisor_info",
            return_value=supervisor_info,
        ),
    ):
        assert await async_setup_component(hass, DOMAIN, {})

        client = await hass_ws_client(hass)

        await client.send_json({"id": 1, "type": "repairs/list_issues"})
        msg = await client.receive_json()
        assert msg["success"]
        assert msg["result"] == {
            "issues": [
                {
                    "breaks_in_ha_version": None,
                    "created": ANY,
                    "dismissed_version": None,
                    "domain": DOMAIN,
                    "ignored": False,
                    "is_fixable": False,
                    "issue_id": f"{alert}.markdown_{integration}",
                    "issue_domain": integration,
                    "learn_more_url": None,
                    "severity": "warning",
                    "translation_key": "alert",
                    "translation_placeholders": {
                        "title": f"Title for {alert}",
                        "description": f"Content for {alert}",
                    },
                }
                for alert, integration in initial_alerts
            ]
        }

    with (
        patch(
            "homeassistant.components.homeassistant_alerts.coordinator.__version__",
            ha_version,
        ),
        patch(
            "homeassistant.components.homeassistant_alerts.coordinator.is_hassio",
            return_value=supervisor_info is not None,
        ),
        patch(
            "homeassistant.components.homeassistant_alerts.coordinator.get_supervisor_info",
            return_value=supervisor_info,
        ),
    ):
        # Fake component_loaded events and wait for debounce
        for domain in late_components:
            hass.config.components.add(domain)
            hass.bus.async_fire(EVENT_COMPONENT_LOADED, {ATTR_COMPONENT: domain})
        freezer.tick(COMPONENT_LOADED_COOLDOWN + 1)
        await hass.async_block_till_done()

        client = await hass_ws_client(hass)

        await client.send_json({"id": 2, "type": "repairs/list_issues"})
        msg = await client.receive_json()
        assert msg["success"]
        assert msg["result"] == {
            "issues": [
                {
                    "breaks_in_ha_version": None,
                    "created": ANY,
                    "dismissed_version": None,
                    "domain": DOMAIN,
                    "ignored": False,
                    "is_fixable": False,
                    "issue_id": f"{alert}.markdown_{integration}",
                    "issue_domain": integration,
                    "learn_more_url": None,
                    "severity": "warning",
                    "translation_key": "alert",
                    "translation_placeholders": {
                        "title": f"Title for {alert}",
                        "description": f"Content for {alert}",
                    },
                }
                for alert, integration in late_alerts
            ]
        }