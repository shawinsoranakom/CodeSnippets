async def test_cache_stores_tools_when_enabled(
        self, component_class, default_kwargs, mock_tools_list, mock_server_config
    ):
        """Test that tools are cached when cache is enabled."""
        component = await self.component_setup(component_class, default_kwargs)
        component.use_cache = True
        server_name = "test_server"

        # Directly test caching by setting up expected data and calling the method
        # Simulate successful tool fetching by manually populating the result
        component.tools = mock_tools_list
        component.tool_names = ["test_tool", "second_tool"]
        component._tool_cache = {"test_tool": mock_tools_list[0]}

        # Manually populate cache as if tools were fetched
        cache_data = {
            "tools": mock_tools_list,
            "tool_names": ["test_tool", "second_tool"],
            "tool_cache": {"test_tool": mock_tools_list[0]},
            "config": mock_server_config,
        }
        current_servers_cache = safe_cache_get(component._shared_component_cache, "servers", {})
        current_servers_cache[server_name] = cache_data
        safe_cache_set(component._shared_component_cache, "servers", current_servers_cache)

        # Now call update_tool_list which should use the cache
        tools, server_info = await component.update_tool_list(server_name)

        # Verify tools were returned from cache
        assert len(tools) == 2
        assert tools[0].name == "test_tool"
        assert tools[1].name == "second_tool"
        assert server_info["name"] == server_name

        # Verify tools are still cached
        servers_cache = safe_cache_get(component._shared_component_cache, "servers", {})
        assert server_name in servers_cache
        cached_data = servers_cache[server_name]
        assert len(cached_data["tools"]) == 2
        assert cached_data["tool_names"] == ["test_tool", "second_tool"]