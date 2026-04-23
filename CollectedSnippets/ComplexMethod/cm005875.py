def test_init_creates_cache_dispatcher(self):
        """Test that __init__ creates the cache flow dispatcher."""
        component = RunFlowBaseComponent()

        assert hasattr(component, "_cache_flow_dispatcher")
        assert isinstance(component._cache_flow_dispatcher, dict)
        assert "get" in component._cache_flow_dispatcher
        assert "set" in component._cache_flow_dispatcher
        assert "delete" in component._cache_flow_dispatcher
        assert "_build_key" in component._cache_flow_dispatcher
        assert "_build_graph" in component._cache_flow_dispatcher