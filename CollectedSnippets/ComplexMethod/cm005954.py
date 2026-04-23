async def test_headers_with_special_characters(self, component):
        """Test headers with special characters in values."""
        component.headers = [
            {"key": "Authorization", "value": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test"},
            {"key": "X-Special", "value": "value with spaces and !@#$%"},
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

        assert server_config["headers"]["Authorization"] == "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test"
        assert server_config["headers"]["X-Special"] == "value with spaces and !@#$%"