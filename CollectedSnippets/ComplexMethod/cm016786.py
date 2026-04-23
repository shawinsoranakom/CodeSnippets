async def _check_providers_lookup(self, node_id, cache_key):
        from comfy_execution.cache_provider import (
            _has_cache_providers, _get_cache_providers,
            CacheValue, _contains_self_unequal, _logger
        )

        if not self.enable_providers:
            return None
        if not _has_cache_providers():
            return None
        if _contains_self_unequal(cache_key):
            return None

        context = self._build_context(node_id, cache_key)
        if context is None:
            return None

        for provider in _get_cache_providers():
            try:
                if not provider.should_cache(context):
                    continue
                result = await provider.on_lookup(context)
                if result is not None:
                    if not isinstance(result, CacheValue):
                        _logger.warning(f"Provider {provider.__class__.__name__} returned invalid type")
                        continue
                    if not isinstance(result.outputs, (list, tuple)):
                        _logger.warning(f"Provider {provider.__class__.__name__} returned invalid outputs")
                        continue
                    from execution import CacheEntry
                    return CacheEntry(ui=result.ui, outputs=list(result.outputs))
            except Exception as e:
                _logger.warning(f"Cache provider {provider.__class__.__name__} error on lookup: {e}")

        return None