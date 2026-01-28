async def webhook_ingress_generic(
    request: Request,
    provider: Annotated[
        ProviderName, Path(title="Provider where the webhook was registered")
    ],
    webhook_id: Annotated[str, Path(title="Our ID for the webhook")],
):
    logger.debug(f"Received {provider.value} webhook ingress for ID {webhook_id}")
    webhook_manager = get_webhook_manager(provider)
    try:
        webhook = await get_webhook(webhook_id, include_relations=True)
        user_id = webhook.user_id
        credentials = (
            await creds_manager.get(user_id, webhook.credentials_id)
            if webhook.credentials_id
            else None
        )
    except NotFoundError as e:
        logger.warning(f"Webhook payload received for unknown webhook #{webhook_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    logger.debug(f"Webhook #{webhook_id}: {webhook}")
    payload, event_type = await webhook_manager.validate_payload(
        webhook, request, credentials
    )
    logger.debug(
        f"Validated {provider.value} {webhook.webhook_type} {event_type} event "
        f"with payload {payload}"
    )

    webhook_event = WebhookEvent(
        provider=provider,
        webhook_id=webhook_id,
        event_type=event_type,
        payload=payload,
    )
    await publish_webhook_event(webhook_event)
    logger.debug(f"Webhook event published: {webhook_event}")

    if not (webhook.triggered_nodes or webhook.triggered_presets):
        return

    await complete_onboarding_step(user_id, OnboardingStep.TRIGGER_WEBHOOK)

    # Execute all triggers concurrently for better performance
    tasks = []
    tasks.extend(
        _execute_webhook_node_trigger(node, webhook, webhook_id, event_type, payload)
        for node in webhook.triggered_nodes
    )
    tasks.extend(
        _execute_webhook_preset_trigger(
            preset, webhook, webhook_id, event_type, payload
        )
        for preset in webhook.triggered_presets
    )

    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
