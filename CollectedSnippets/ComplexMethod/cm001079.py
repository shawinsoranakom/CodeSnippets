def test_inserts_converter_for_incompatible_types(self):
        fixer = AgentFixer()
        src_block_id = generate_uuid()
        sink_block_id = generate_uuid()

        src_node = _make_node(node_id="src", block_id=src_block_id)
        sink_node = _make_node(node_id="sink", block_id=sink_block_id)
        link = _make_link(
            source_id="src",
            source_name="result",
            sink_id="sink",
            sink_name="count",
        )
        agent = _make_agent(nodes=[src_node, sink_node], links=[link])

        blocks = [
            self._make_block(
                src_block_id,
                name="Source",
                output_schema={"properties": {"result": {"type": "string"}}},
            ),
            self._make_block(
                sink_block_id,
                name="Sink",
                input_schema={"properties": {"count": {"type": "integer"}}},
            ),
        ]

        result = fixer.fix_data_type_mismatch(agent, blocks)

        # A converter node should have been inserted
        converter_nodes = [
            n
            for n in result["nodes"]
            if n["block_id"] == _UNIVERSAL_TYPE_CONVERTER_BLOCK_ID
        ]
        assert len(converter_nodes) == 1
        assert converter_nodes[0]["input_default"]["type"] == "number"

        # Original link replaced by two new links through the converter
        assert len(result["links"]) == 2
        src_to_converter = result["links"][0]
        converter_to_sink = result["links"][1]

        assert src_to_converter["source_id"] == "src"
        assert src_to_converter["sink_id"] == converter_nodes[0]["id"]
        assert src_to_converter["sink_name"] == "value"

        assert converter_to_sink["source_id"] == converter_nodes[0]["id"]
        assert converter_to_sink["source_name"] == "value"
        assert converter_to_sink["sink_id"] == "sink"
        assert converter_to_sink["sink_name"] == "count"

        assert len(fixer.fixes_applied) == 1