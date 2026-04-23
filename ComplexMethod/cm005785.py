def test_expand_simple_flow(self):
        compact_data = {
            "nodes": [
                {"id": "1", "type": "ChatInput"},
                {"id": "2", "type": "OpenAIModel", "values": {"model_name": "gpt-4"}},
                {"id": "3", "type": "ChatOutput"},
            ],
            "edges": [
                {
                    "source": "1",
                    "source_output": "message",
                    "target": "2",
                    "target_input": "input_value",
                },
                {
                    "source": "2",
                    "source_output": "text_output",
                    "target": "3",
                    "target_input": "input_value",
                },
            ],
        }

        expanded = expand_compact_flow(compact_data, SAMPLE_COMPONENTS)

        assert len(expanded["nodes"]) == 3
        assert len(expanded["edges"]) == 2

        # Check nodes are properly expanded
        node_types = {n["data"]["type"] for n in expanded["nodes"]}
        assert node_types == {"ChatInput", "OpenAIModel", "ChatOutput"}

        # Check values were merged
        openai_node = next(n for n in expanded["nodes"] if n["data"]["type"] == "OpenAIModel")
        assert openai_node["data"]["node"]["template"]["model_name"]["value"] == "gpt-4"