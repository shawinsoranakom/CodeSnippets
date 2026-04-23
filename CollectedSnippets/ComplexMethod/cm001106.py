async def migrate_legacy_triggered_graphs():
    from prisma.models import AgentGraph

    from backend.api.features.library.db import create_preset
    from backend.api.features.library.model import LibraryAgentPresetCreatable
    from backend.data.graph import AGENT_GRAPH_INCLUDE, GraphModel, set_node_webhook
    from backend.data.model import is_credentials_field_name

    triggered_graphs = [
        GraphModel.from_db(_graph)
        for _graph in await AgentGraph.prisma().find_many(
            where={
                "isActive": True,
                "Nodes": {"some": {"NOT": [{"webhookId": None}]}},
            },
            include=AGENT_GRAPH_INCLUDE,
        )
    ]

    n_migrated_webhooks = 0

    for graph in triggered_graphs:
        try:
            if not (
                (trigger_node := graph.webhook_input_node) and trigger_node.webhook_id
            ):
                continue

            # Use trigger node's inputs for the preset
            preset_credentials = {
                field_name: creds_meta
                for field_name, creds_meta in trigger_node.input_default.items()
                if is_credentials_field_name(field_name)
            }
            preset_inputs = {
                field_name: value
                for field_name, value in trigger_node.input_default.items()
                if not is_credentials_field_name(field_name)
            }

            # Create a triggered preset for the graph
            await create_preset(
                graph.user_id,
                LibraryAgentPresetCreatable(
                    graph_id=graph.id,
                    graph_version=graph.version,
                    inputs=preset_inputs,
                    credentials=preset_credentials,
                    name=graph.name,
                    description=graph.description,
                    webhook_id=trigger_node.webhook_id,
                    is_active=True,
                ),
            )

            # Detach webhook from the graph node
            await set_node_webhook(trigger_node.id, None)

            n_migrated_webhooks += 1
        except Exception as e:
            logger.error(f"Failed to migrate graph #{graph.id} trigger to preset: {e}")
            continue

    logger.info(f"Migrated {n_migrated_webhooks} node triggers to triggered presets")