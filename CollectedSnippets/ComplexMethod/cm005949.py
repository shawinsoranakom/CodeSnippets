async def test_headers_merge_empty_list(self, component):
        """Test that empty headers list doesn't modify server config."""
        component.headers = []

        server_config = {
            "url": "http://test.url",
            "headers": {"X-Existing": "value"},
        }

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

        # Should remain unchanged
        assert server_config["headers"] == {"X-Existing": "value"}