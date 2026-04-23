async def fix_llm_provider_credentials():
    """Fix node credentials with provider `llm`"""
    from backend.integrations.credentials_store import IntegrationCredentialsStore

    from .user import get_user_integrations

    store = IntegrationCredentialsStore()

    broken_nodes = []
    try:
        broken_nodes = await query_raw_with_schema(
            """
            SELECT    graph."userId"       user_id,
                  node.id              node_id,
                  node."constantInput" node_preset_input
            FROM      {schema_prefix}"AgentNode"  node
            LEFT JOIN {schema_prefix}"AgentGraph" graph
            ON        node."agentGraphId" = graph.id
            WHERE     node."constantInput"::jsonb->'credentials'->>'provider' = 'llm'
            ORDER BY  graph."userId";
            """
        )
        logger.info(f"Fixing LLM credential inputs on {len(broken_nodes)} nodes")
    except Exception as e:
        logger.error(f"Error fixing LLM credential inputs: {e}")

    user_id: str = ""
    user_integrations = None
    for node in broken_nodes:
        if node["user_id"] != user_id:
            # Save queries by only fetching once per user
            user_id = node["user_id"]
            user_integrations = await get_user_integrations(user_id)
        elif not user_integrations:
            raise RuntimeError(f"Impossible state while processing node {node}")

        node_id: str = node["node_id"]
        node_preset_input: dict = node["node_preset_input"]
        credentials_meta: dict = node_preset_input["credentials"]

        credentials = next(
            (
                c
                for c in user_integrations.credentials
                if c.id == credentials_meta["id"]
            ),
            None,
        )
        if not credentials:
            continue
        if credentials.type != "api_key":
            logger.warning(
                f"User {user_id} credentials {credentials.id} with provider 'llm' "
                f"has invalid type '{credentials.type}'"
            )
            continue

        api_key = credentials.api_key.get_secret_value()
        if api_key.startswith("sk-ant-api03-"):
            credentials.provider = credentials_meta["provider"] = "anthropic"
        elif api_key.startswith("sk-"):
            credentials.provider = credentials_meta["provider"] = "openai"
        elif api_key.startswith("gsk_"):
            credentials.provider = credentials_meta["provider"] = "groq"
        else:
            logger.warning(
                f"Could not identify provider from key prefix {api_key[:13]}*****"
            )
            continue

        await store.update_creds(user_id, credentials)
        await AgentNode.prisma().update(
            where={"id": node_id},
            data={"constantInput": SafeJson(node_preset_input)},
        )