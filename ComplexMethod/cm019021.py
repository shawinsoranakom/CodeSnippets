async def test_legacy_subscription_repair_flow(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    hass_client: ClientSessionGenerator,
    issue_registry: ir.IssueRegistry,
) -> None:
    """Test desired flow of the fix flow for legacy subscription."""
    aioclient_mock.get(
        "https://api.nabucasa.com/account/payments/subscription_info",
        json={"provider": None},
    )
    aioclient_mock.post(
        "https://api.nabucasa.com/account/payments/migrate_paypal_agreement",
        json={"url": "https://paypal.com"},
    )

    async_manage_legacy_subscription_issue(hass, {"provider": "legacy"})
    repair_issue = issue_registry.async_get_issue(
        domain="cloud", issue_id="legacy_subscription"
    )
    assert repair_issue

    assert await async_setup_component(hass, REPAIRS_DOMAIN, {REPAIRS_DOMAIN: {}})
    await mock_cloud(hass)
    await hass.async_block_till_done()
    await hass.async_start()

    client = await hass_client()

    resp = await client.post(
        "/api/repairs/issues/fix",
        json={"handler": DOMAIN, "issue_id": repair_issue.issue_id},
    )

    assert resp.status == HTTPStatus.OK
    data = await resp.json()

    flow_id = data["flow_id"]
    assert data == {
        "type": "form",
        "flow_id": flow_id,
        "handler": DOMAIN,
        "step_id": "confirm_change_plan",
        "data_schema": [],
        "errors": None,
        "description_placeholders": None,
        "last_step": None,
        "preview": None,
    }

    resp = await client.post(f"/api/repairs/issues/fix/{flow_id}")

    assert resp.status == HTTPStatus.OK
    data = await resp.json()

    flow_id = data["flow_id"]
    assert data == {
        "type": "external",
        "flow_id": flow_id,
        "handler": DOMAIN,
        "step_id": "change_plan",
        "url": "https://paypal.com",
        "description_placeholders": None,
    }

    resp = await client.post(f"/api/repairs/issues/fix/{flow_id}")

    assert resp.status == HTTPStatus.OK
    data = await resp.json()

    flow_id = data["flow_id"]
    assert data == {
        "type": "create_entry",
        "flow_id": flow_id,
        "handler": DOMAIN,
        "description": None,
        "description_placeholders": None,
    }

    assert not issue_registry.async_get_issue(
        domain="cloud", issue_id="legacy_subscription"
    )