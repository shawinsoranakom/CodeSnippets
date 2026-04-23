async def _execute_webhook_preset_trigger(
    preset: LibraryAgentPreset,
    webhook: WebhookWithRelations,
    webhook_id: str,
    event_type: str,
    payload: dict,
) -> None:
    """Execute a webhook-triggered preset."""
    logger.debug(f"Webhook-attached preset: {preset}")
    if not preset.is_active:
        logger.debug(f"Preset #{preset.id} is inactive")
        return

    graph = await get_graph(
        preset.graph_id, preset.graph_version, user_id=webhook.user_id
    )
    if not graph:
        logger.error(
            f"User #{webhook.user_id} has preset #{preset.id} for graph "
            f"#{preset.graph_id} v{preset.graph_version}, "
            "but no access to the graph itself."
        )
        logger.info(f"Automatically deactivating broken preset #{preset.id}")
        await update_preset(preset.user_id, preset.id, is_active=False)
        return
    if not (trigger_node := graph.webhook_input_node):
        # NOTE: this should NEVER happen, but we log and handle it gracefully
        logger.error(
            f"Preset #{preset.id} is triggered by webhook #{webhook.id}, but graph "
            f"#{preset.graph_id} v{preset.graph_version} has no webhook input node"
        )
        await set_preset_webhook(preset.user_id, preset.id, None)
        return
    if not trigger_node.block.is_triggered_by_event_type(preset.inputs, event_type):
        logger.debug(f"Preset #{preset.id} doesn't trigger on event {event_type}")
        return
    logger.debug(f"Executing preset #{preset.id} for webhook #{webhook.id}")

    try:
        await add_graph_execution(
            user_id=webhook.user_id,
            graph_id=preset.graph_id,
            preset_id=preset.id,
            graph_version=preset.graph_version,
            graph_credentials_inputs=preset.credentials,
            nodes_input_masks={trigger_node.id: {**preset.inputs, "payload": payload}},
        )
    except GraphNotInLibraryError as e:
        logger.warning(
            f"Webhook #{webhook_id} execution blocked for "
            f"deleted/archived graph #{preset.graph_id} (preset #{preset.id}): {e}"
        )
        # Clean up orphaned webhook trigger for this graph
        await _cleanup_orphaned_webhook_for_graph(
            preset.graph_id, webhook.user_id, webhook_id
        )
    except Exception:
        logger.exception(
            f"Failed to execute preset #{preset.id} via webhook #{webhook_id}"
        )
        # Continue processing - webhook should be resilient to individual failures
