def test_multiple_tools_streaming(self, parser):
        full_text = (
            f"{FC_START}\n"
            f'{INV_START}func_a">\n'
            f'{PARAM_START}p" string="true">v1{PARAM_END}\n'
            f"{INV_END}\n"
            f'{INV_START}func_b">\n'
            f'{PARAM_START}q" string="true">v2{PARAM_END}\n'
            f"{INV_END}\n"
            f"{FC_END}"
        )
        deltas = self._stream(parser, full_text)

        # Collect function names by index
        names_by_index: dict[int, str] = {}
        for d in deltas:
            if d.tool_calls:
                for tc in d.tool_calls:
                    if tc.function and tc.function.name:
                        names_by_index[tc.index] = tc.function.name

        assert names_by_index.get(0) == "func_a"
        assert names_by_index.get(1) == "func_b"

        assert json.loads(self._reconstruct_args(deltas, tool_index=0)) == {"p": "v1"}
        assert json.loads(self._reconstruct_args(deltas, tool_index=1)) == {"q": "v2"}