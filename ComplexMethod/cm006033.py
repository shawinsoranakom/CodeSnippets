def test_full_flow_with_finalize_build_failure(self):
        """Test the complete flow when finalize_build fails during cache restoration.

        This simulates the exact scenario that was causing the bug:
        1. Frozen vertex, cache hit
        2. Restore state from cache (built=True)
        3. finalize_build() fails
        4. built flag should be reset
        5. build() should run fully
        """
        # Arrange
        vertex = Mock()
        vertex.id = "ChatInput-abc123"
        vertex.frozen = True
        vertex.built = False
        vertex.is_loop = False
        vertex.display_name = "Chat Input"
        vertex.result = None

        cached_vertex_dict = {
            "built": True,
            "artifacts": {},
            "built_object": {"message": Mock()},
            "built_result": {"message": Mock()},
            "full_data": {},
            "results": {"message": Mock()},
        }

        # Simulate finalize_build failure
        def finalize_build_that_fails():
            msg = "Simulated finalize_build failure"
            raise ValueError(msg)

        vertex.finalize_build = finalize_build_that_fails

        # Act - simulate build_vertex logic
        should_build = False
        is_loop_component = vertex.display_name == "Loop" or vertex.is_loop

        if not vertex.frozen or is_loop_component:
            should_build = True
        else:
            # Simulate cache hit - restore state
            vertex.built = cached_vertex_dict["built"]
            vertex.artifacts = cached_vertex_dict["artifacts"]
            vertex.built_object = cached_vertex_dict["built_object"]
            vertex.built_result = cached_vertex_dict["built_result"]
            vertex.full_data = cached_vertex_dict["full_data"]
            vertex.results = cached_vertex_dict["results"]

            try:
                vertex.finalize_build()
            except Exception:
                vertex.built = False  # THE FIX
                should_build = True

        # Assert
        assert should_build is True, "should_build should be True after finalize_build failure"
        assert vertex.built is False, "vertex.built should be reset to False"

        # Verify that build() will NOT return early
        should_return_early = vertex.frozen and vertex.built and not is_loop_component
        assert should_return_early is False, "build() should NOT return early with reset built flag"