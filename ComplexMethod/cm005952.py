async def test_headers_merge_dict_format_fallback(self, component):
        """Test that dict format still works as fallback."""
        # Even though we use is_list=True, the code also supports dict format
        component.headers = {
            "Authorization": "Bearer dict-token",
            "X-Dict-Header": "dict-value",
        }

        server_config = {"url": "http://test.url"}

        component_headers = getattr(component, "headers", None) or []
        component_headers_dict = {}
        if isinstance(component_headers, list):
            for item in component_headers:
                if isinstance(item, dict) and "key" in item and "value" in item:
                    component_headers_dict[item["key"]] = item["value"]
        elif isinstance(component_headers, dict):
            component_headers_dict = component_headers

        if component_headers_dict:
            existing_headers = server_config.get("headers", {}) or {}
            merged_headers = {**existing_headers, **component_headers_dict}
            server_config["headers"] = merged_headers

        assert server_config["headers"] == {
            "Authorization": "Bearer dict-token",
            "X-Dict-Header": "dict-value",
        }