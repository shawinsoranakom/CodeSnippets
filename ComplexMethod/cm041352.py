def test_trace_id_logic(self):
        headers = Headers({"x-amzn-trace-id": "Root=trace;Parent=parent"})
        trace = InvocationRequestParser.populate_trace_id(headers)
        assert trace == "Root=trace;Parent=parent;Sampled=1"

        no_trace_headers = Headers()
        trace = InvocationRequestParser.populate_trace_id(no_trace_headers)
        parsed_trace = parse_trace_id(trace)
        assert len(parsed_trace["Root"]) == 35
        assert len(parsed_trace["Parent"]) == 16
        assert parsed_trace["Sampled"] == "0"

        no_parent_headers = Headers({"x-amzn-trace-id": "Root=trace"})
        trace = InvocationRequestParser.populate_trace_id(no_parent_headers)
        parsed_trace = parse_trace_id(trace)
        assert parsed_trace["Root"] == "trace"
        assert len(parsed_trace["Parent"]) == 16
        assert parsed_trace["Sampled"] == "0"