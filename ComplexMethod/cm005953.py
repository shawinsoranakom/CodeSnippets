async def test_headers_merge_existing_headers_as_list(self, component):
        """Test merging when existing headers are also in list format."""
        component.headers = [
            {"key": "New-Header", "value": "new-value"},
        ]

        server_config = {
            "url": "http://test.url",
            "headers": [
                {"key": "Existing-Header", "value": "existing-value"},
            ],
        }

        component_headers = getattr(component, "headers", None) or []
        component_headers_dict = {}
        if isinstance(component_headers, list):
            for item in component_headers:
                if isinstance(item, dict) and "key" in item and "value" in item:
                    component_headers_dict[item["key"]] = item["value"]

        if component_headers_dict:
            existing_headers = server_config.get("headers", {}) or {}
            # Convert existing headers from list to dict if needed
            if isinstance(existing_headers, list):
                existing_dict = {}
                for item in existing_headers:
                    if isinstance(item, dict) and "key" in item and "value" in item:
                        existing_dict[item["key"]] = item["value"]
                existing_headers = existing_dict
            merged_headers = {**existing_headers, **component_headers_dict}
            server_config["headers"] = merged_headers

        assert server_config["headers"] == {
            "Existing-Header": "existing-value",
            "New-Header": "new-value",
        }