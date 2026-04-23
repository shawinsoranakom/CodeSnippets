def create_provider(
        cls,
        name: str,
        provider: Union[Type[BaseProvider], str],
        base_url: str = None,
        api_key: str = None,
        **kwargs
    ) -> Type[BaseProvider]:
        """
        Register a live/custom provider that can be used by name.

        Args:
            name: Name to register the provider under
            provider: Either a provider class or "custom" to create a custom provider
            base_url: Base URL for custom providers
            api_key: API key for custom providers
            **kwargs: Additional arguments for custom provider creation

        Returns:
            The registered provider class
        """
        if not isinstance(provider, str):
            return provider
        elif provider.startswith("custom:"):
            if provider.startswith("custom:"):
                serverId = provider[7:]
                base_url = f"https://g4f.space/custom/{serverId}"
            if not base_url:
                raise ValueError("base_url is required for custom providers")
            provider = create_custom_provider(base_url, api_key, name=name, **kwargs)
        elif provider in ProviderUtils.convert:
            provider = ProviderUtils.convert[provider]
        else:
            if not cls._live_providers:
                path = Path(get_cookies_dir()) / "models" / datetime.today().strftime('%Y-%m-%d') / f"providers.json"
                path.parent.mkdir(parents=True, exist_ok=True)
                if path.exists():
                    with open(path, "r", encoding="utf-8") as f:
                        cls._live_providers = json.load(f)
                cls._live_providers = requests.get(cls._live_providers_url).json()
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(cls._live_providers, f, indent=4)
            if provider in cls._live_providers.get("providers", {}):
                config = cls._live_providers["providers"][provider]
                if "provider" in config and config.get("provider") in ProviderUtils.convert:
                    return ProviderUtils.convert[config.get("provider")]
                return create_custom_provider(
                    base_url=config.get("baseUrl") if api_key else config.get("backupUrl", config.get("baseUrl")),
                    api_key=api_key,
                    name=provider,
                    default_model=cls._live_providers["defaultModels"].get(provider, ""),
                )
            else:
                raise ProviderNotFoundError(f"Provider '{name}' not found")
        return provider