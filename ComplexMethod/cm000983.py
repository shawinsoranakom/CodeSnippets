async def match_user_credentials_to_graph(
    user_id: str,
    graph: GraphModel,
) -> tuple[dict[str, CredentialsMetaInput], list[str]]:
    """
    Match user's available credentials against graph's required credentials.

    Uses graph.aggregate_credentials_inputs() which handles credentials from
    multiple nodes and uses frozensets for provider matching.

    Args:
        user_id: The user's ID
        graph: The Graph with credential requirements

    Returns:
        tuple[matched_credentials dict, missing_credential_descriptions list]
    """
    graph_credentials_inputs: dict[str, CredentialsMetaInput] = {}
    missing_creds: list[str] = []

    # Get aggregated credentials requirements from the graph
    aggregated_creds = graph.aggregate_credentials_inputs()
    logger.debug(
        f"Matching credentials for graph {graph.id}: {len(aggregated_creds)} required"
    )

    if not aggregated_creds:
        return graph_credentials_inputs, missing_creds

    # Get all available credentials for the user
    creds_manager = IntegrationCredentialsManager()
    available_creds = await creds_manager.store.get_all_creds(user_id)

    # For each required credential field, find a matching user credential
    # field_info.provider is a frozenset because aggregate_credentials_inputs()
    # combines requirements from multiple nodes. A credential matches if its
    # provider is in the set of acceptable providers.
    for credential_field_name, (
        credential_requirements,
        _,
        _,
    ) in aggregated_creds.items():
        # Find first matching credential by provider, type, scopes, and host/URL
        matching_cred = next(
            (
                cred
                for cred in available_creds
                if cred.provider in credential_requirements.provider
                and cred.type in credential_requirements.supported_types
                and (
                    cred.type != "oauth2"
                    or _credential_has_required_scopes(cred, credential_requirements)
                )
                and (
                    cred.type != "host_scoped"
                    or _credential_is_for_host(cred, credential_requirements)
                )
                and (
                    cred.provider != ProviderName.MCP
                    or _credential_is_for_mcp_server(cred, credential_requirements)
                )
            ),
            None,
        )

        if matching_cred:
            try:
                graph_credentials_inputs[credential_field_name] = CredentialsMetaInput(
                    id=matching_cred.id,
                    provider=matching_cred.provider,  # type: ignore
                    type=matching_cred.type,
                    title=matching_cred.title,
                )
            except Exception as e:
                logger.error(
                    f"Failed to create CredentialsMetaInput for field '{credential_field_name}': "
                    f"provider={matching_cred.provider}, type={matching_cred.type}, "
                    f"credential_id={matching_cred.id}",
                    exc_info=True,
                )
                missing_creds.append(
                    f"{credential_field_name} (validation failed: {e})"
                )
        else:
            # Build a helpful error message including scope requirements
            error_parts = [
                f"provider in {list(credential_requirements.provider)}",
                f"type in {list(credential_requirements.supported_types)}",
            ]
            if credential_requirements.required_scopes:
                error_parts.append(
                    f"scopes including {list(credential_requirements.required_scopes)}"
                )
            missing_creds.append(
                f"{credential_field_name} (requires {', '.join(error_parts)})"
            )

    logger.info(
        f"Credential matching complete: {len(graph_credentials_inputs)}/{len(aggregated_creds)} matched"
    )

    return graph_credentials_inputs, missing_creds