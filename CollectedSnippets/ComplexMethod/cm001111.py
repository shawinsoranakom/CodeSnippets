async def test_responses_api_tool_pairs_preserved(self):
        """Responses API function_call / function_call_output pairs must
        survive compaction intact.  Currently they can be silently deleted
        because _is_tool_message doesn't recognise them."""
        messages = [
            {"role": "system", "content": "You are helpful."},
        ]
        # Add enough messages to trigger compaction
        for i in range(20):
            messages.append({"role": "user", "content": f"Question {i} " * 200})
            messages.append({"role": "assistant", "content": f"Answer {i} " * 200})
        # Add a Responses API tool pair at the end
        messages.append(
            {
                "type": "function_call",
                "id": "fc_final",
                "call_id": "call_final",
                "name": "search_tool",
                "arguments": '{"q": "test"}',
                "status": "completed",
            }
        )
        messages.append(
            {
                "type": "function_call_output",
                "call_id": "call_final",
                "output": '{"results": ["a", "b"]}',
            }
        )
        messages.append({"role": "user", "content": "Thanks!"})

        result = await compress_context(messages, target_tokens=2000, client=None)

        # The function_call and function_call_output must both survive
        fc_items = [m for m in result.messages if m.get("type") == "function_call"]
        fco_items = [
            m for m in result.messages if m.get("type") == "function_call_output"
        ]

        # If either exists, the other must exist too (pair integrity)
        if fc_items or fco_items:
            fc_call_ids = {m["call_id"] for m in fc_items}
            fco_call_ids = {m["call_id"] for m in fco_items}
            assert (
                fco_call_ids <= fc_call_ids
            ), "function_call_output exists without matching function_call"

        # At minimum, neither should have been silently deleted if the
        # conversation was short enough to keep them
        assert len(fc_items) >= 1, "function_call was deleted during compaction"
        assert len(fco_items) >= 1, "function_call_output was deleted during compaction"