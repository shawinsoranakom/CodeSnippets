async def test_execute_real_flow_with_results(self, simple_chat_py):
        """Test executing a real flow and extracting results."""
        # Load the real graph
        graph = await load_graph_from_script(simple_chat_py)

        # Execute the graph with real input
        from lfx.graph.schema import RunOutputs

        # Start the graph execution
        results = [result async for result in graph.async_start(inputs={"input_value": "Test message"})]

        # Extract results using our functions
        if isinstance(results, RunOutputs) and results.outputs:
            # Convert RunOutputs to the format expected by extract functions
            result_list = []
            for output in results.outputs:
                mock_result = MagicMock()
                mock_result.vertex.custom_component.display_name = output.component_display_name
                mock_result.vertex.id = output.component_id
                mock_result.result_dict = output
                result_list.append(mock_result)

            # Test extraction functions with real results
            text = extract_text_from_result(result_list)
            assert "Test message" in text

            message_json = extract_message_from_result(result_list)
            assert "Test message" in message_json

            structured = extract_structured_result(result_list)
            assert structured["success"] is True
            assert "Test message" in str(structured["result"])