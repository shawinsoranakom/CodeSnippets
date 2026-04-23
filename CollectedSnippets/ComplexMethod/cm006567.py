def test_flow_has_valid_structure(self):
        spec = """\
name: Structure Test

nodes:
  A: ChatInput
  B: ChatOutput

edges:
  A.message -> B.input_value
"""
        result = build_flow_from_spec(spec)
        assert "flow" in result
        flow = result["flow"]
        assert "data" in flow
        assert "nodes" in flow["data"]
        assert "edges" in flow["data"]
        assert "viewport" in flow["data"]
        # Each node should have proper Langflow structure
        for node in flow["data"]["nodes"]:
            assert "data" in node
            assert "id" in node["data"]
            assert "type" in node["data"]
            assert "node" in node["data"]
            assert "template" in node["data"]["node"]