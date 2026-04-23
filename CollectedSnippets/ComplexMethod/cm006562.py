def test_frontend_node_generation(self, component_class, default_kwargs):
        """Test frontend node generation."""
        component = component_class(**default_kwargs)

        frontend_node = component.to_frontend_node()

        # Verify node structure
        if frontend_node is None:
            pytest.fail("frontend_node is None")
        if not isinstance(frontend_node, dict):
            pytest.fail(f"Expected frontend_node to be dict, got {type(frontend_node)}")
        if "data" not in frontend_node:
            pytest.fail("data not found in frontend_node")
        if "type" not in frontend_node["data"]:
            pytest.fail("type not found in frontend_node['data']")

        node_data = frontend_node["data"]["node"]
        if "description" not in node_data:
            pytest.fail("description not found in node_data")
        if "icon" not in node_data:
            pytest.fail("icon not found in node_data")
        if "template" not in node_data:
            pytest.fail("template not found in node_data")

        # Verify template has correct inputs
        template = node_data["template"]
        if "api_key" not in template:
            pytest.fail("api_key not found in template")
        if "media_type" not in template:
            pytest.fail("media_type not found in template")
        if "media_files" not in template:
            pytest.fail("media_files not found in template")
        if "media_url" not in template:
            pytest.fail("media_url not found in template")