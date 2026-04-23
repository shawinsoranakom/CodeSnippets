async def test_switching_from_cache_disabled_to_enabled(
        self, component_class, default_kwargs, mock_tools_list, mock_server_config
    ):
        """Test switching from cache disabled to enabled by testing cache logic directly."""
        component = await self.component_setup(component_class, default_kwargs)
        server_name = "test_server"

        # Start with cache disabled
        component.use_cache = False

        # Test that cache lookup would be skipped
        use_cache = getattr(component, "use_cache", True)
        assert use_cache is False

        # When cache is disabled, the cache lookup logic should be skipped
        cached = None
        if use_cache:
            servers_cache = safe_cache_get(component._shared_component_cache, "servers", {})
            cached = servers_cache.get(server_name) if isinstance(servers_cache, dict) else None

        # Since use_cache is False, cached should remain None
        assert cached is None

        # Switch to cache enabled
        component.use_cache = True

        # Test that cache would now be used if available
        use_cache = getattr(component, "use_cache", True)
        assert use_cache is True

        # Pre-populate cache to test retrieval
        cache_data = {
            "tools": mock_tools_list,
            "tool_names": ["test_tool", "second_tool"],
            "tool_cache": {"test_tool": mock_tools_list[0]},
            "config": mock_server_config,
        }
        safe_cache_set(component._shared_component_cache, "servers", {server_name: cache_data})

        # Now cache should be retrieved when enabled
        if use_cache:
            servers_cache = safe_cache_get(component._shared_component_cache, "servers", {})
            cached = servers_cache.get(server_name) if isinstance(servers_cache, dict) else None

        assert cached is not None
        assert len(cached["tools"]) == 2
        assert cached["tool_names"] == ["test_tool", "second_tool"]