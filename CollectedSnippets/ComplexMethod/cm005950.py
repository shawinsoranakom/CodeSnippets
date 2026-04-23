async def test_headers_merge_none_headers(self, component):
        """Test that None headers doesn't cause errors."""
        component.headers = None

        server_config = {"url": "http://test.url"}

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

        # Should not have headers key added
        assert "headers" not in server_config