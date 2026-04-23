async def create_async_generator(
        self,
        model: str,
        messages: Messages,
        api_key: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> AsyncResult:
        """Yield response chunks, routing through configured providers."""
        last_exception: Optional[Exception] = None
        tried: List[str] = []

        for prc in self._route_config.providers:
            try:
                provider = _resolve_provider(prc.provider)
            except ValueError as e:
                debug.error(f"config.yaml: {e}")
                continue

            provider_name = getattr(provider, "__name__", prc.provider)

            # Fetch quota (cached)
            quota = await _get_quota_cached(provider)

            # Evaluate condition
            if not _check_condition(prc, provider, quota):
                debug.log(
                    f"config.yaml: Skipping {provider_name} "
                    f"(condition not met: {prc.condition!r})"
                )
                continue

            target_model = prc.model or model
            tried.append(provider_name)

            yield ProviderInfo(
                name=provider_name,
                url=getattr(provider, "url", ""),
                label=getattr(provider, "label", None),
                model=target_model,
            )

            extra_body = kwargs.copy()
            current_api_key = api_key.get(provider.get_parent()) if isinstance(api_key, dict) else api_key
            if not current_api_key or AppConfig.disable_custom_api_key:
                current_api_key = AuthManager.load_api_key(provider)
            if current_api_key:
                extra_body["api_key"] = current_api_key

            try:
                if hasattr(provider, "create_async_generator"):
                    async for chunk in provider.create_async_generator(
                        target_model, messages, **extra_body
                    ):
                        yield chunk
                elif hasattr(provider, "create_completion"):
                    for chunk in provider.create_completion(
                        target_model, messages, **extra_body
                    ):
                        yield chunk
                else:
                    raise NotImplementedError(
                        f"{provider_name} has no supported create method"
                    )
                debug.log(f"config.yaml: {provider_name} succeeded for model {model!r}")
                return  # Success
            except Exception as e:
                # On rate-limit errors invalidate the quota cache
                from ..errors import RateLimitError
                if isinstance(e, RateLimitError) or "429" in str(e):
                    debug.log(
                        f"config.yaml: Rate-limited by {provider_name}, "
                        "invalidating quota cache"
                    )
                    QuotaCache.invalidate(provider_name)

                ErrorCounter.increment(provider_name)
                last_exception = e
                debug.error(f"config.yaml: {provider_name} failed:", e)

        if last_exception is not None:
            raise last_exception
        raise RuntimeError(
            f"config.yaml: No provider succeeded for model {model!r}. "
            f"Tried: {tried}"
        )