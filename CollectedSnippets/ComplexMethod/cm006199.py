async def test_persist_flow_tweak_data(self, client, logged_in_headers, active_user):
        """Test that flow tweak data is persisted to the selected subflow on execution with multiple components."""
        # Create a flow with multiple components we can tweak
        text_input_1 = TextInputComponent()
        text_input_1.set_id("input_node_1")
        text_input_1.input_value = "default_value_1"
        text_input_1.is_output = True

        text_input_2 = TextInputComponent()
        text_input_2.set_id("input_node_2")
        text_input_2.input_value = "default_value_2"
        text_input_2.is_output = True

        # We need a graph that can be run
        graph = Graph(start=text_input_1, end=text_input_2)
        graph_dict = graph.dump(name="Multi Tweakable Flow", description="Flow for multi-tweak testing")
        flow = FlowCreate(**graph_dict)

        # Create flow via API
        response = await client.post("api/v1/flows/", json=flow.model_dump(), headers=logged_in_headers)
        assert response.status_code == 201
        flow_data = response.json()
        flow_id = flow_data["id"]
        flow_name = flow_data["name"]

        try:
            # Setup component with real flow
            component = RunFlowComponent()
            component._user_id = str(active_user.id)
            component.flow_name_selected = flow_name
            component.flow_id_selected = flow_id
            component.cache_flow = False  # Disable cache to ensure fresh graph load

            # Set up tweaks for both components
            tweaks = {"input_node_1~input_value": "tweaked_value_1", "input_node_2~input_value": "tweaked_value_2"}
            component.flow_tweak_data = tweaks
            component._attributes = {"flow_tweak_data": tweaks}

            # We execute with the real run_flow to verify tweaks are applied during execution
            result = await component._run_flow_with_cached_graph(user_id=str(active_user.id))

            assert result is not None
            assert len(result) > 0

            # Verify the flow output reflects the tweaked value
            run_output = result[0]

            # Check output for input_node_1
            output_1 = next((o for o in run_output.outputs if o.component_id == "input_node_1"), None)
            assert output_1 is not None, "Did not find output for input_node_1"

            message_1 = output_1.results["text"]
            if hasattr(message_1, "text"):
                assert message_1.text == "tweaked_value_1"
            else:
                assert message_1.get("text") == "tweaked_value_1"

            # Check output for input_node_2
            output_2 = next((o for o in run_output.outputs if o.component_id == "input_node_2"), None)
            assert output_2 is not None, "Did not find output for input_node_2"

            message_2 = output_2.results["text"]
            if hasattr(message_2, "text"):
                assert message_2.text == "tweaked_value_2"
            else:
                assert message_2.get("text") == "tweaked_value_2"

        finally:
            # Cleanup
            await client.delete(f"api/v1/flows/{flow_id}", headers=logged_in_headers)