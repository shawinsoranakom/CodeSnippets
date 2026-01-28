async def _execute_webhook_node_trigger(
    node: NodeModel,
    webhook: WebhookWithRelations,
    webhook_id: str,
    event_type: str,
    payload: dict,
) -> None:
    """Execute a webhook-triggered node."""
    logger.debug(f"Webhook-attached node: {node}")
    if not node.is_triggered_by_event_type(event_type):
        logger.debug(f"Node #{node.id} doesn't trigger on event {event_type}")
        return
    logger.debug(f"Executing graph #{node.graph_id} node #{node.id}")
    try:
        await add_graph_execution(
            user_id=webhook.user_id,
            graph_id=node.graph_id,
            graph_version=node.graph_version,
            nodes_input_masks={node.id: {"payload": payload}},
        )
    except GraphNotInLibraryError as e:
        logger.warning(
            f"Webhook #{webhook_id} execution blocked for "
            f"deleted/archived graph #{node.graph_id} (node #{node.id}): {e}"
        )
        # Clean up orphaned webhook trigger for this graph
        await _cleanup_orphaned_webhook_for_graph(
            node.graph_id, webhook.user_id, webhook_id
        )
    except Exception:
        logger.exception(
            f"Failed to execute graph #{node.graph_id} via webhook #{webhook_id}"
        )
