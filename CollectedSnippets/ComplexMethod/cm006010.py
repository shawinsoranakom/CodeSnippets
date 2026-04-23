def test_component_has_subgraph_methods(self):
        """Test that LoopComponent has the new subgraph execution methods."""
        loop = LoopComponent()

        # Check that new methods exist
        assert hasattr(loop, "get_loop_body_vertices")
        assert hasattr(loop, "execute_loop_body")
        assert hasattr(loop, "_get_loop_body_start_vertex")
        assert hasattr(loop, "_extract_loop_output")

        # Check that methods are callable
        assert callable(loop.get_loop_body_vertices)
        assert callable(loop.execute_loop_body)
        assert callable(loop._get_loop_body_start_vertex)
        assert callable(loop._extract_loop_output)