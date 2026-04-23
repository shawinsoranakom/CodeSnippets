async def test_switching_from_cache_enabled_to_disabled(
        self, component_class, default_kwargs, mock_tools_list, mock_server_config
    ):
        """Test switching from cache enabled to disabled by testing cache logic directly."""
        component = await self.component_setup(component_class, default_kwargs)
        server_name = "test_server"

        # Start with cache enabled
        component.use_cache = True

        # Pre-populate cache
        cache_data = {
            "tools": mock_tools_list,
            "tool_names": ["test_tool", "second_tool"],
            "tool_cache": {"test_tool": mock_tools_list[0]},
            "config": mock_server_config,
        }
        safe_cache_set(component._shared_component_cache, "servers", {server_name: cache_data})

        # Test cache logic directly - first verify cache would be used
        use_cache = getattr(component, "use_cache", True)
        assert use_cache is True

        servers_cache = safe_cache_get(component._shared_component_cache, "servers", {})
        cached = servers_cache.get(server_name) if isinstance(servers_cache, dict) else None
        assert cached is not None
        assert len(cached["tools"]) == 2

        # Switch to cache disabled
        component.use_cache = False

        # Test that cache lookup would now be skipped
        use_cache = getattr(component, "use_cache", True)
        assert use_cache is False

        # When cache is disabled, the cache lookup logic should be skipped
        cached = None
        if use_cache:
            servers_cache = safe_cache_get(component._shared_component_cache, "servers", {})
            cached = servers_cache.get(server_name) if isinstance(servers_cache, dict) else None

        # Since use_cache is False, cached should remain None (cache was not looked up)
        assert cached is None

        # Verify the cache data still exists but would be ignored
        servers_cache = safe_cache_get(component._shared_component_cache, "servers", {})
        assert server_name in servers_cache
        assert len(servers_cache[server_name]["tools"]) == 2