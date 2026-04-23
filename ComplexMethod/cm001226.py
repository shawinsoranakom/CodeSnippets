async def remove_all_webhooks_for_credentials(
    user_id: str, credentials: Credentials, force: bool = False
) -> None:
    """
    Remove and deregister all webhooks that were registered using the given credentials.

    Params:
        user_id: The ID of the user who owns the credentials and webhooks.
        credentials: The credentials for which to remove the associated webhooks.
        force: Whether to proceed if any of the webhooks are still in use.

    Raises:
        NeedConfirmation: If any of the webhooks are still in use and `force` is `False`
    """
    webhooks = await get_all_webhooks_by_creds(
        user_id, credentials.id, include_relations=True
    )
    if any(w.triggered_nodes or w.triggered_presets for w in webhooks) and not force:
        raise NeedConfirmation(
            "Some webhooks linked to these credentials are still in use by an agent"
        )
    for webhook in webhooks:
        # Unlink all nodes & presets
        for node in webhook.triggered_nodes:
            await set_node_webhook(node.id, None)
        for preset in webhook.triggered_presets:
            await set_preset_webhook(user_id, preset.id, None)

        # Prune the webhook
        webhook_manager = get_webhook_manager(ProviderName(credentials.provider))
        success = await webhook_manager.prune_webhook_if_dangling(
            user_id, webhook.id, credentials
        )
        if not success:
            logger.warning(f"Webhook #{webhook.id} failed to prune")