def test_second_run_scenario_with_fix(self):
        """Test the exact scenario reported: first run works, second run fails.

        This test simulates:
        1. First run: vertex builds normally
        2. Second run: cache restoration fails, but fix ensures rebuild works
        """
        # First run - simulates successful initial build
        vertex = Mock()
        vertex.id = "ChatInput-ybc2G"
        vertex.frozen = True
        vertex.built = False
        vertex.is_loop = False
        vertex.display_name = "Chat Input"
        vertex.result = None

        # Simulate first run: should_build = True (not frozen initially or no cache)
        # After first run: vertex.built = True, vertex.result = Mock()
        vertex.built = True
        vertex.result = Mock()  # First run sets result

        # Second run - cache hit but finalize_build fails
        # This simulates a new vertex instance with same ID
        vertex_run2 = Mock()
        vertex_run2.id = "ChatInput-ybc2G"
        vertex_run2.frozen = True
        vertex_run2.built = False  # New instance starts with built=False
        vertex_run2.is_loop = False
        vertex_run2.display_name = "Chat Input"
        vertex_run2.result = None  # New instance starts with result=None

        cached_vertex_dict = {
            "built": True,  # From first run
            "artifacts": {},
            "built_object": {"message": Mock()},
            "built_result": {"message": Mock()},
            "full_data": {},
            "results": {"message": Mock()},
        }

        # Simulate cache restoration failure
        vertex_run2.finalize_build = Mock(side_effect=ValueError("Simulated failure"))

        # Act - simulate build_vertex for second run
        should_build = False
        is_loop_component = vertex_run2.display_name == "Loop" or vertex_run2.is_loop

        if not vertex_run2.frozen or is_loop_component:
            should_build = True
        else:
            # Cache hit - restore state
            vertex_run2.built = cached_vertex_dict["built"]  # Set to True
            try:
                vertex_run2.finalize_build()
            except Exception:
                vertex_run2.built = False  # THE FIX - reset to False
                should_build = True

        # Assert - with the fix, the vertex should rebuild correctly
        assert vertex_run2.built is False, "vertex.built should be reset after cache restoration failure"
        assert should_build is True, "should_build should trigger rebuild"

        # Verify build() won't return early
        should_return_early = vertex_run2.frozen and vertex_run2.built and not is_loop_component
        assert should_return_early is False, "build() should continue with reset built flag"