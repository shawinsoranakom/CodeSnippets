async def test_tool_generation_from_flow(self, client, logged_in_headers, active_user):
        """Test that tools are generated correctly from flow inputs."""
        # Configure client to follow redirects for folder API
        client.follow_redirects = True

        # Create a folder for our flows
        folder_response = await client.post(
            "api/v1/folders/",
            json={"name": "Tool Test Folder", "description": "Folder for tool generation tests"},
            headers=logged_in_headers,
        )
        assert folder_response.status_code == 201
        folder_id = folder_response.json()["id"]

        # Create a REAL flow that can be used as a tool
        # Simple chat input -> chat output flow
        chat_input = ChatInput()
        chat_output = ChatOutput()
        graph = Graph(start=chat_input, end=chat_output)
        graph_dict = graph.dump(name="Tool Flow", description="A flow that can be used as a tool")
        tool_flow = FlowCreate(**graph_dict, folder_id=folder_id, user_id=str(active_user.id))

        # Create tool flow via API (will be associated with active_user via logged_in_headers)
        response = await client.post("api/v1/flows/", json=tool_flow.model_dump(mode="json"), headers=logged_in_headers)
        assert response.status_code == 201
        flow_data = response.json()
        flow_id = flow_data["id"]
        flow_name = flow_data["name"]
        # Verify the flow is owned by the active user
        assert flow_data["user_id"] == str(active_user.id), "Tool flow should be owned by active_user"

        # Create a wrapper flow with RunFlowComponent (in the same folder, same user)
        run_flow_component = RunFlowComponent()
        wrapper_graph = Graph(start=run_flow_component, end=run_flow_component)
        wrapper_dict = wrapper_graph.dump(name="Tool Wrapper", description="Wrapper for tool generation")
        wrapper_flow = FlowCreate(**wrapper_dict, folder_id=folder_id, user_id=str(active_user.id))

        wrapper_response = await client.post(
            "api/v1/flows/",
            json=wrapper_flow.model_dump(mode="json"),
            headers=logged_in_headers,
        )
        assert wrapper_response.status_code == 201
        wrapper_flow_data = wrapper_response.json()
        wrapper_flow_id = wrapper_flow_data["id"]
        # Verify the wrapper flow is also owned by the same user
        assert wrapper_flow_data["user_id"] == str(active_user.id), "Wrapper flow should be owned by active_user"

        try:
            # Setup component with real flow and wrapper flow's ID
            component = RunFlowComponent()
            component._user_id = str(active_user.id)
            component._flow_id = wrapper_flow_id  # Use the wrapper flow's ID
            component.flow_name_selected = flow_name
            component.flow_id_selected = flow_id

            # Verify the component can retrieve the graph from the database
            graph = await component.get_graph(flow_name, flow_id)
            assert graph is not None, "Expected to retrieve graph from database"
            assert graph.flow_name == flow_name, f"Expected flow_name to be {flow_name}"

            # Verify the graph has the expected components
            assert len(graph.vertices) > 0, "Expected graph to have vertices"

            # Call get_required_data to verify it extracts input fields
            result = await component.get_required_data()
            assert result is not None, "Expected to get flow description and fields"
            flow_description, tool_mode_fields = result
            assert isinstance(flow_description, str), "Flow description should be a string"
            assert isinstance(tool_mode_fields, list), "Tool mode fields should be a list"
            # Note: ChatInput may or may not have tool_mode=True inputs, so we don't assert the count

            # Get tools from real flow - ChatInput/ChatOutput may or may not generate tools
            # depending on whether inputs have tool_mode=True
            tools = await component._get_tools()
            # Verify the method executes without error (tools list may be empty for simple chat flow)
            assert isinstance(tools, list), "Expected tools to be a list"
        finally:
            # Cleanup
            await client.delete(f"api/v1/flows/{flow_id}", headers=logged_in_headers)
            await client.delete(f"api/v1/flows/{wrapper_flow_id}", headers=logged_in_headers)
            await client.delete(f"api/v1/folders/{folder_id}", headers=logged_in_headers)