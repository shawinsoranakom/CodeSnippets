async def test_legacy_subscription_repair_flow_timeout(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    issue_registry: ir.IssueRegistry,
) -> None:
    """Test timeout flow of the fix flow for legacy subscription."""
    aioclient_mock.post(
        "https://accounts.nabucasa.com/payments/migrate_paypal_agreement",
        status=403,
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

    with (
        patch("homeassistant.components.cloud.repairs.MAX_RETRIES", new=0),
        patch(
            "hass_nabucasa.payments_api.PaymentsApi.migrate_paypal_agreement",
            side_effect=PaymentsApiError("some error", status=403),
        ),
    ):
        resp = await client.post(f"/api/repairs/issues/fix/{flow_id}")
        assert resp.status == HTTPStatus.OK
        data = await resp.json()

        flow_id = data["flow_id"]
        assert data == {
            "type": "external",
            "flow_id": flow_id,
            "handler": DOMAIN,
            "step_id": "change_plan",
            "url": "https://account.nabucasa.com/",
            "description_placeholders": None,
        }

    resp = await client.post(f"/api/repairs/issues/fix/{flow_id}")
    assert resp.status == HTTPStatus.OK
    data = await resp.json()

    flow_id = data["flow_id"]
    assert data == {
        "type": "abort",
        "flow_id": flow_id,
        "handler": "cloud",
        "reason": "operation_took_too_long",
        "description_placeholders": None,
    }

    assert issue_registry.async_get_issue(
        domain="cloud", issue_id="legacy_subscription"
    )