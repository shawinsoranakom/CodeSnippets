def build_mcp_providers(
    recipe: dict[str, Any],
) -> list:
    from data_designer.config.mcp import LocalStdioMCPProvider, MCPProvider

    providers: list[MCPProvider | LocalStdioMCPProvider] = []
    for provider in recipe.get("mcp_providers", []):
        if not isinstance(provider, dict):
            continue
        provider_type = provider.get("provider_type")
        if provider_type == "stdio":
            env = provider.get("env")
            if not isinstance(env, dict):
                env = {}
            args = provider.get("args")
            if not isinstance(args, list):
                args = []
            providers.append(
                LocalStdioMCPProvider(
                    name = str(provider.get("name", "")),
                    command = str(provider.get("command", "")),
                    args = [str(value) for value in args],
                    env = {str(key): str(value) for key, value in env.items()},
                )
            )
            continue

        if provider_type in {"sse", "streamable_http"}:
            api_key = provider.get("api_key")
            api_key_env = provider.get("api_key_env")
            if not api_key and api_key_env:
                api_key = os.getenv(str(api_key_env))
            providers.append(
                MCPProvider(
                    name = str(provider.get("name", "")),
                    endpoint = str(provider.get("endpoint", "")),
                    provider_type = str(provider_type),
                    api_key = str(api_key) if api_key else None,
                )
            )
    return providers