async def test_auto_multi_tool_streaming_opens_one_item_per_tool(self, monkeypatch):
        monkeypatch.setattr(envs, "VLLM_USE_EXPERIMENTAL_PARSER_CONTEXT", False)

        delta_sequence = [
            DeltaMessage(
                tool_calls=[
                    DeltaToolCall(
                        id="call_vienna",
                        type="function",
                        index=0,
                        function=DeltaFunctionCall(
                            name="get_weather",
                            arguments="",
                        ),
                    )
                ]
            ),
            DeltaMessage(
                tool_calls=[
                    DeltaToolCall(
                        index=0,
                        function=DeltaFunctionCall(
                            arguments='{"location":"Vienna"}',
                        ),
                    )
                ]
            ),
            DeltaMessage(
                tool_calls=[
                    DeltaToolCall(
                        id="call_berlin",
                        type="function",
                        index=1,
                        function=DeltaFunctionCall(
                            name="get_weather",
                            arguments='{"location":"Berlin"}',
                        ),
                    )
                ]
            ),
        ]
        events = await self._collect_events(delta_sequence)

        function_items = [
            event
            for event in events
            if event.type == "response.output_item.added"
            and getattr(event.item, "type", None) == "function_call"
        ]
        assert len(function_items) == 2
        assert [event.item.name for event in function_items] == [
            "get_weather",
            "get_weather",
        ]
        assert [event.output_index for event in function_items] == [0, 1]

        argument_deltas = [
            event.delta
            for event in events
            if event.type == "response.function_call_arguments.delta"
        ]
        assert argument_deltas == [
            '{"location":"Vienna"}',
            '{"location":"Berlin"}',
        ]

        argument_done = [
            event
            for event in events
            if event.type == "response.function_call_arguments.done"
        ]
        assert [event.arguments for event in argument_done] == [
            '{"location":"Vienna"}',
            '{"location":"Berlin"}',
        ]
        assert [event.output_index for event in argument_done] == [0, 1]

        function_done = [
            event
            for event in events
            if event.type == "response.output_item.done"
            and getattr(event.item, "type", None) == "function_call"
        ]
        assert [event.item.arguments for event in function_done] == [
            '{"location":"Vienna"}',
            '{"location":"Berlin"}',
        ]
        assert [event.output_index for event in function_done] == [0, 1]