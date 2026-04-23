def test_expand_edge_source_handle_format(self):
        """Test that sourceHandle is a JSON-encoded dict with œ as quotes."""
        compact_edge = CompactEdge(
            source="node1",
            source_output="message",
            target="node2",
            target_input="input_value",
        )
        expanded_nodes = {
            "node1": {
                "id": "node1",
                "type": "genericNode",
                "data": {
                    "type": "ChatInput",
                    "node": SAMPLE_COMPONENTS["inputs"]["ChatInput"],
                },
            },
            "node2": {
                "id": "node2",
                "type": "genericNode",
                "data": {
                    "type": "OpenAIModel",
                    "node": SAMPLE_COMPONENTS["models"]["OpenAIModel"],
                },
            },
        }

        expanded = _expand_edge(compact_edge, expanded_nodes)

        # sourceHandle is JSON-encoded with œ as quotes
        source_handle = expanded["sourceHandle"]
        assert "œdataTypeœ" in source_handle
        assert "œChatInputœ" in source_handle
        assert "œnode1œ" in source_handle
        assert "œmessageœ" in source_handle
        assert "œMessageœ" in source_handle

        # data.sourceHandle is the actual dict
        source_data = expanded["data"]["sourceHandle"]
        assert source_data["dataType"] == "ChatInput"
        assert source_data["id"] == "node1"
        assert source_data["name"] == "message"
        assert source_data["output_types"] == ["Message"]