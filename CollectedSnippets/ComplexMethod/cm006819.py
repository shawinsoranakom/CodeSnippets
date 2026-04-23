def _flow_cache_call(self, action: str, *args, **kwargs):
        """Call a flow cache related method."""
        if not self.cache_flow:
            msg = "Cache flow is disabled"
            logger.warning(msg)
            return None
        if self._shared_component_cache is None:
            logger.warning("Shared component cache is not available")
            return None

        handler = self._cache_flow_dispatcher.get(action)
        if handler is None:
            msg = f"Unknown cache action: {action}"
            raise ValueError(msg)
        try:
            return handler(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001
            key = kwargs.get("cache_key") or kwargs.get("flow_name") or kwargs.get("flow_name_selected")
            if not key and args:
                key = args[0]
            logger.warning("Cache %s failed for key %s: %s", action, key or "[missing key]", exc)
            return None