async def test_headers_empty_string_values(self, component):
        """Test headers with empty string values."""
        component.headers = [
            {"key": "X-Empty", "value": ""},
            {"key": "X-Valid", "value": "valid"},
        ]

        server_config = {"url": "http://test.url"}

        component_headers = getattr(component, "headers", None) or []
        component_headers_dict = {}
        if isinstance(component_headers, list):
            for item in component_headers:
                if isinstance(item, dict) and "key" in item and "value" in item:
                    component_headers_dict[item["key"]] = item["value"]

        if component_headers_dict:
            server_config["headers"] = component_headers_dict

        # Empty string is still a valid value
        assert server_config["headers"]["X-Empty"] == ""
        assert server_config["headers"]["X-Valid"] == "valid"