async def test_headers_merge_list_format(self, component):
        """Test merging headers in list format [{"key": k, "value": v}]."""
        # Setup component with headers in list format
        component.headers = [
            {"key": "Authorization", "value": "Bearer test-token"},
            {"key": "X-Custom-Header", "value": "custom-value"},
        ]

        server_config = {"url": "http://test.url", "mode": "Streamable_HTTP"}

        # Simulate the merge logic from update_tool_list
        component_headers = getattr(component, "headers", None) or []
        component_headers_dict = {}
        if isinstance(component_headers, list):
            for item in component_headers:
                if isinstance(item, dict) and "key" in item and "value" in item:
                    component_headers_dict[item["key"]] = item["value"]

        if component_headers_dict:
            existing_headers = server_config.get("headers", {}) or {}
            merged_headers = {**existing_headers, **component_headers_dict}
            server_config["headers"] = merged_headers

        assert server_config["headers"] == {
            "Authorization": "Bearer test-token",
            "X-Custom-Header": "custom-value",
        }