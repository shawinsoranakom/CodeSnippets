async def auth_manager_from_config(
    hass: HomeAssistant,
    provider_configs: list[dict[str, Any]],
    module_configs: list[dict[str, Any]],
) -> AuthManager:
    """Initialize an auth manager from config.

    CORE_CONFIG_SCHEMA will make sure no duplicated auth providers or
    mfa modules exist in configs.
    """
    store = auth_store.AuthStore(hass)
    await store.async_load()
    if provider_configs:
        providers = await asyncio.gather(
            *(
                auth_provider_from_config(hass, store, config)
                for config in provider_configs
            )
        )
    else:
        providers = []
    # So returned auth providers are in same order as config
    provider_hash: _ProviderDict = OrderedDict()
    for provider in providers:
        key = (provider.type, provider.id)
        provider_hash[key] = provider

        if isinstance(provider, HassAuthProvider):
            # Can be removed in 2026.7 with the legacy mode of homeassistant auth provider
            # We need to initialize the provider to create the repair if needed as otherwise
            # the provider will be initialized on first use, which could be rare as users
            # don't frequently change auth settings
            await provider.async_initialize()

    if module_configs:
        modules = await asyncio.gather(
            *(auth_mfa_module_from_config(hass, config) for config in module_configs)
        )
    else:
        modules = []
    # So returned auth modules are in same order as config
    module_hash: _MfaModuleDict = OrderedDict()
    for module in modules:
        module_hash[module.id] = module

    manager = AuthManager(hass, store, provider_hash, module_hash)
    await manager.async_setup()
    return manager