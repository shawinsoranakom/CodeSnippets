def test_multi_turn_with_thinking_blocks(self):
        """Full multi-turn conversation: previous assistant messages that
        include thinking blocks must all be converted without a 400 error.

        This is the primary regression scenario from the bug report:
        upgrading vllm from v0.15.1 → v0.17.0 introduced thinking-block
        support in responses, but echoing those responses back in subsequent
        requests caused a Pydantic validation failure.
        """
        request = _make_request(
            [
                {"role": "user", "content": "Turn 1 question"},
                {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "thinking",
                            "thinking": "Reasoning for turn 1.",
                            "signature": "s_t1",
                        },
                        {"type": "text", "text": "Answer for turn 1."},
                    ],
                },
                {"role": "user", "content": "Turn 2 question"},
                {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "thinking",
                            "thinking": "Reasoning for turn 2.",
                            "signature": "s_t2",
                        },
                        {"type": "text", "text": "Answer for turn 2."},
                    ],
                },
                {"role": "user", "content": "Turn 3 question"},
            ]
        )
        # Must not raise a ValidationError / 400.
        result = _convert(request)

        asst_msgs = [m for m in result.messages if m.get("role") == "assistant"]
        assert len(asst_msgs) == 2

        assert asst_msgs[0].get("reasoning") == "Reasoning for turn 1."
        assert asst_msgs[0].get("content") == "Answer for turn 1."
        assert asst_msgs[1].get("reasoning") == "Reasoning for turn 2."
        assert asst_msgs[1].get("content") == "Answer for turn 2."