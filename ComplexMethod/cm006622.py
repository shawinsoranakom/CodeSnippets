async def test_loop_item_injection_via_execute_loop_body(self):
        """Test that execute_loop_body actually injects loop items into vertex raw_params.

        This is an integration-style test that exercises the actual loop_utils.py code path,
        verifying that update_raw_params() is called with loop items during execution.
        """
        from unittest.mock import MagicMock

        from lfx.schema.data import Data

        # Track calls to update_raw_params
        update_raw_params_calls = []

        def mock_update_raw_params(params, overwrite=False):  # noqa: FBT002
            update_raw_params_calls.append((params, overwrite))

        # Create mock vertex that tracks update_raw_params calls
        mock_start_vertex = MagicMock()
        mock_start_vertex.id = "start_vertex"
        mock_start_vertex.custom_component = MagicMock()
        mock_start_vertex.update_raw_params = mock_update_raw_params

        # Create mock subgraph
        def create_mock_subgraph(_vertex_ids):
            mock_subgraph = MagicMock()
            mock_subgraph._vertices = [
                {"id": "start_vertex", "data": {"node": {"template": {"input_data": {"value": None}}}}}
            ]
            mock_subgraph.prepare = MagicMock()
            mock_subgraph.get_vertex = MagicMock(return_value=mock_start_vertex)

            # Mock async_start to yield valid results
            async def mock_async_start(**_kwargs):
                yield MagicMock(valid=True, result_dict=MagicMock(outputs={}))

            mock_subgraph.async_start = mock_async_start
            return mock_subgraph

        mock_graph = MagicMock()
        mock_graph.create_subgraph = create_subgraph_context_manager_mock(create_mock_subgraph)

        # Test data
        data_list = [
            Data(text="First item"),
            Data(text="Second item"),
        ]

        # Mock edge with field_name
        mock_edge = MagicMock()
        mock_edge.target_handle.field_name = "input_data"

        # Execute loop body
        await execute_loop_body(
            graph=mock_graph,
            data_list=data_list,
            loop_body_vertex_ids={"start_vertex"},
            start_vertex_id="start_vertex",
            start_edge=mock_edge,
            end_vertex_id="start_vertex",
            event_manager=None,
        )

        # Verify update_raw_params was called for each loop item
        assert len(update_raw_params_calls) == 2, "Should call update_raw_params for each loop iteration"

        # Verify first call had first item
        first_call_params, first_call_overwrite = update_raw_params_calls[0]
        assert "input_data" in first_call_params
        assert first_call_params["input_data"].text == "First item"
        assert first_call_overwrite is True

        # Verify second call had second item
        second_call_params, second_call_overwrite = update_raw_params_calls[1]
        assert "input_data" in second_call_params
        assert second_call_params["input_data"].text == "Second item"
        assert second_call_overwrite is True