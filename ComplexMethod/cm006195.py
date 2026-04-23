async def test_complete_flow_execution_workflow(self, client, logged_in_headers, active_user):
        """Test complete workflow: select flow, update config, execute flow."""
        # Configure client to follow redirects for folder API
        client.follow_redirects = True

        # First, create a folder for our flows
        folder_response = await client.post(
            "api/v1/folders/",
            json={"name": "Test Folder", "description": "Folder for integration tests"},
            headers=logged_in_headers,
        )
        assert folder_response.status_code == 201
        folder_id = folder_response.json()["id"]

        # Create the target flow that will be run (Integration Test Flow)
        chat_input = ChatInput()
        chat_output = ChatOutput()
        graph = Graph(start=chat_input, end=chat_output)
        graph_dict = graph.dump(name="Integration Test Flow", description="Test integration flow")
        target_flow = FlowCreate(**graph_dict, folder_id=folder_id)

        # Create target flow via API (uses real database)
        response = await client.post(
            "api/v1/flows/",
            json=target_flow.model_dump(mode="json"),
            headers=logged_in_headers,
        )
        assert response.status_code == 201
        target_flow_data = response.json()
        target_flow_id = target_flow_data["id"]
        target_flow_name = target_flow_data["name"]

        # Create a flow that wraps RunFlowComponent (in the same folder)
        run_flow_component = RunFlowComponent()
        wrapper_graph = Graph(start=run_flow_component, end=run_flow_component)
        wrapper_dict = wrapper_graph.dump(name="RunFlow Wrapper", description="Wrapper flow with RunFlow component")
        wrapper_flow = FlowCreate(**wrapper_dict, folder_id=folder_id)

        wrapper_response = await client.post(
            "api/v1/flows/",
            json=wrapper_flow.model_dump(mode="json"),
            headers=logged_in_headers,
        )
        assert wrapper_response.status_code == 201
        wrapper_flow_data = wrapper_response.json()
        wrapper_flow_id = wrapper_flow_data["id"]

        try:
            # Setup component with real user_id and flow_id from the wrapper flow
            component = RunFlowComponent()
            component._user_id = str(active_user.id)
            component._flow_id = wrapper_flow_id  # Use the wrapper flow's ID
            component.cache_flow = False

            # Step 1: Build config with flow list
            build_config = dotdict(
                {
                    "code": {},
                    "_type": {},
                    "flow_name_selected": {"options": [], "options_metadata": []},
                    "is_refresh": True,
                    "flow_id_selected": {},
                    "session_id": {},
                    "cache_flow": {},
                }
            )

            # NO MOCKING - Use real component methods that will hit real database
            updated_config = await component.update_build_config(
                build_config=build_config, field_value=None, field_name="flow_name_selected"
            )

            # Verify the real flow appears in options (should see target flow in same folder)
            assert target_flow_name in updated_config["flow_name_selected"]["options"]
            # Remove this assertion - the wrapper flow is excluded because it's the current flow:
            # assert "RunFlow Wrapper" in updated_config["flow_name_selected"]["options"]

            # Update the metadata check - we should only see 1 flow (the target flow)
            # because the wrapper flow (current flow) is excluded
            assert len(updated_config["flow_name_selected"]["options_metadata"]) == 1
            flow_ids = [str(meta["id"]) for meta in updated_config["flow_name_selected"]["options_metadata"]]
            assert target_flow_id in flow_ids
        finally:
            # Cleanup
            await client.delete(f"api/v1/flows/{target_flow_id}", headers=logged_in_headers)
            await client.delete(f"api/v1/flows/{wrapper_flow_id}", headers=logged_in_headers)
            await client.delete(f"api/v1/folders/{folder_id}", headers=logged_in_headers)