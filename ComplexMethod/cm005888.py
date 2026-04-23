def test_should_preserve_all_blocks_in_mixed_image_and_resource_result(self):
        """Mixed image + resource must produce a list with both blocks, nothing dropped."""
        import json

        from lfx.base.mcp.util import _convert_mcp_result

        b64 = "abc123=="
        image = self._make_image_block(data=b64, mime="image/png")
        resource = self._make_resource_block(uri="file:///chart.csv")
        result = self._make_result([image, resource])

        converted = _convert_mcp_result(result)

        assert isinstance(converted, list)
        assert len(converted) == 2

        # First block: image
        assert converted[0]["type"] == "image_url"
        assert converted[0]["image_url"]["url"] == f"data:image/png;base64,{b64}"

        # Second block: resource serialised as text
        assert converted[1]["type"] == "text"
        parsed = json.loads(converted[1]["text"])
        assert parsed["type"] == "resource"
        assert parsed["uri"] == "file:///chart.csv"