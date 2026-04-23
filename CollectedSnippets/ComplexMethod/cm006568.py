def test_basic_spec(self):
        spec = """\
name: Test Flow
description: A test

nodes:
  A: ChatInput
  B: ChatOutput

edges:
  A.message -> B.input_value
"""
        result = parse_flow_spec(spec)
        assert result["name"] == "Test Flow"
        assert result["description"] == "A test"
        assert len(result["nodes"]) == 2
        assert result["nodes"][0] == {"id": "A", "type": "ChatInput"}
        assert result["nodes"][1] == {"id": "B", "type": "ChatOutput"}
        assert len(result["edges"]) == 1
        assert result["edges"][0] == {
            "source_id": "A",
            "source_output": "message",
            "target_id": "B",
            "target_input": "input_value",
        }