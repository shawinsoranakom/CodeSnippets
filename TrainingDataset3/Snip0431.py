async def _cleanup_orphaned_webhook_for_graph(
    graph_id: str, user_id: str, webhook_id: str
) -> None:
    """
    Clean up orphaned webhook connections for a specific graph when execution fails with GraphNotAccessibleError.
    This happens when an agent is pulled from the Marketplace or deleted
    but webhook triggers still exist.
    """
    try:
        webhook = await get_webhook(webhook_id, include_relations=True)
        if not webhook or webhook.user_id != user_id:
            logger.warning(
                f"Webhook {webhook_id} not found or doesn't belong to user {user_id}"
            )
            return

        nodes_removed = 0
        presets_removed = 0

        # Remove triggered nodes that belong to the deleted graph
        for node in webhook.triggered_nodes:
            if node.graph_id == graph_id:
                try:
                    await set_node_webhook(node.id, None)
                    nodes_removed += 1
                    logger.info(
                        f"Removed orphaned webhook trigger from node {node.id} "
                        f"in deleted/archived graph {graph_id}"
                    )
                except Exception:
                    logger.exception(
                        f"Failed to remove webhook trigger from node {node.id}"
                    )

        # Remove triggered presets that belong to the deleted graph
        for preset in webhook.triggered_presets:
            if preset.graph_id == graph_id:
                try:
                    await set_preset_webhook(user_id, preset.id, None)
                    presets_removed += 1
                    logger.info(
                        f"Removed orphaned webhook trigger from preset {preset.id} "
                        f"for deleted/archived graph {graph_id}"
                    )
                except Exception:
                    logger.exception(
                        f"Failed to remove webhook trigger from preset {preset.id}"
                    )

        if nodes_removed > 0 or presets_removed > 0:
            logger.info(
                f"Cleaned up orphaned webhook #{webhook_id}: "
                f"removed {nodes_removed} nodes and {presets_removed} presets "
                f"for deleted/archived graph #{graph_id}"
            )

            # Check if webhook has any remaining triggers, if not, prune it
            updated_webhook = await get_webhook(webhook_id, include_relations=True)
            if (
                not updated_webhook.triggered_nodes
                and not updated_webhook.triggered_presets
            ):
                try:
                    webhook_manager = get_webhook_manager(
                        ProviderName(webhook.provider)
                    )
                    credentials = (
                        await creds_manager.get(user_id, webhook.credentials_id)
                        if webhook.credentials_id
                        else None
                    )
                    success = await webhook_manager.prune_webhook_if_dangling(
                        user_id, webhook.id, credentials
                    )
                    if success:
                        logger.info(
                            f"Pruned orphaned webhook #{webhook_id} "
                            f"with no remaining triggers"
                        )
                    else:
                        logger.warning(
                            f"Failed to prune orphaned webhook #{webhook_id}"
                        )
                except Exception:
                    logger.exception(f"Failed to prune orphaned webhook #{webhook_id}")

    except Exception:
        logger.exception(
            f"Failed to cleanup orphaned webhook #{webhook_id} for graph #{graph_id}"
        )
