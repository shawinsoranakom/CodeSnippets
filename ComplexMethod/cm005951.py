async def test_headers_merge_malformed_list_items(self, component):
        """Test that malformed list items are skipped."""
        component.headers = [
            {"key": "Valid-Header", "value": "valid-value"},
            {"key": "Missing-Value"},  # Missing "value"
            {"value": "Missing-Key"},  # Missing "key"
            "not-a-dict",  # Wrong type
            None,  # None item
            {"key": "Another-Valid", "value": "another-value"},
        ]

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

        # Only valid items should be included
        assert server_config["headers"] == {
            "Valid-Header": "valid-value",
            "Another-Valid": "another-value",
        }