def test_expand_edge_target_handle_format(self):
        """Test that targetHandle is a JSON-encoded dict with œ as quotes."""
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

        # targetHandle is JSON-encoded with œ as quotes
        target_handle = expanded["targetHandle"]
        assert "œfieldNameœ" in target_handle
        assert "œinput_valueœ" in target_handle
        assert "œnode2œ" in target_handle
        assert "œMessageœ" in target_handle

        # data.targetHandle is the actual dict
        target_data = expanded["data"]["targetHandle"]
        assert target_data["fieldName"] == "input_value"
        assert target_data["id"] == "node2"
        assert target_data["inputTypes"] == ["Message"]
        assert target_data["type"] == "Message"