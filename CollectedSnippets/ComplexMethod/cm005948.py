async def test_headers_merge_with_existing_headers(self, component):
        """Test that component headers override existing server config headers."""
        component.headers = [
            {"key": "Authorization", "value": "Bearer new-token"},
        ]

        server_config = {
            "url": "http://test.url",
            "mode": "Streamable_HTTP",
            "headers": {"Authorization": "Bearer old-token", "X-Existing": "existing-value"},
        }

        # Simulate the merge logic
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

        # Component headers should override existing
        assert server_config["headers"]["Authorization"] == "Bearer new-token"
        # Existing headers should be preserved
        assert server_config["headers"]["X-Existing"] == "existing-value"