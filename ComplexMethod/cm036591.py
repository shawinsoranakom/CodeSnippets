def test_tool_call_fields(self, parser):
        """Each emitted tool call has id, name, arguments, type, index."""
        results = _feed(
            parser,
            [
                '<minimax:tool_call><invoke name="fn">'
                '<parameter name="k">v</parameter>'
                "</invoke></minimax:tool_call>",
            ],
        )
        tc_deltas = [tc for r in results for tc in (r.tool_calls or [])]
        assert len(tc_deltas) == 1
        tc = tc_deltas[0]
        assert tc.index == 0
        assert tc.type == "function"
        assert tc.id is not None and tc.id.startswith("call_")
        assert tc.function.name == "fn"
        assert json.loads(tc.function.arguments) == {"k": "v"}