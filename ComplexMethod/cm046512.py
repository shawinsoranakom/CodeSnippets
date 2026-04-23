def test_tool_end_closes_tool_opens_new_text_block(self):
        e = AnthropicStreamEmitter()
        e.start("msg_1", "m")
        e.feed(
            {
                "type": "tool_start",
                "tool_name": "t",
                "tool_call_id": "tc_1",
                "arguments": {},
            }
        )
        events = e.feed(
            {
                "type": "tool_end",
                "tool_name": "t",
                "tool_call_id": "tc_1",
                "result": "done",
            }
        )
        # content_block_stop (tool) + tool_result + content_block_start (new text)
        assert len(events) == 3
        assert "content_block_stop" in events[0]
        assert "tool_result" in events[1]
        parsed = json.loads(events[1].split("data: ")[1])
        assert parsed["content"] == "done"
        assert parsed["tool_use_id"] == "tc_1"
        assert "content_block_start" in events[2]
        assert '"type": "text"' in events[2]