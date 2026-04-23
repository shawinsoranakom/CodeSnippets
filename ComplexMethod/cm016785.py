async def _notify_providers_store(self, node_id, cache_key, value):
        from comfy_execution.cache_provider import (
            _has_cache_providers, _get_cache_providers,
            CacheValue, _contains_self_unequal, _logger
        )

        if not self.enable_providers:
            return
        if not _has_cache_providers():
            return
        if not self._is_external_cacheable_value(value):
            return
        if _contains_self_unequal(cache_key):
            return

        context = self._build_context(node_id, cache_key)
        if context is None:
            return
        cache_value = CacheValue(outputs=value.outputs, ui=value.ui)

        for provider in _get_cache_providers():
            try:
                if provider.should_cache(context, cache_value):
                    task = asyncio.create_task(self._safe_provider_store(provider, context, cache_value))
                    self._pending_store_tasks.add(task)
                    task.add_done_callback(self._pending_store_tasks.discard)
            except Exception as e:
                _logger.warning(f"Cache provider {provider.__class__.__name__} error on store: {e}")