def test_chat_multi_turn_streaming(self):
        tool_def = self._get_tool_def()

        # Turn 1: streaming — accumulate tool call from deltas
        chunks = list(
            self.client.chat.completions.create(
                model=self.MODEL,
                messages=[{"role": "user", "content": "What is the weather in Paris?"}],
                stream=True,
                max_tokens=50,
                temperature=0.0,
                tools=[tool_def],
            )
        )
        self.assertEqual(chunks[-1].choices[0].finish_reason, "tool_calls")
        tool_chunks = [c for c in chunks if c.choices[0].delta.tool_calls]
        self.assertGreater(len(tool_chunks), 0)
        tc = tool_chunks[0].choices[0].delta.tool_calls[0]

        # Reconstruct assistant message from deltas
        content = "".join(c.choices[0].delta.content for c in chunks if c.choices[0].delta.content)
        assistant_msg = {
            "role": "assistant",
            "content": content,
            "tool_calls": [{"id": tc.id, "type": "function", "function": tc.function.model_dump()}],
        }

        # Turn 2: streaming — send back tool result
        chunks2 = list(
            self.client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {"role": "user", "content": "What is the weather in Paris?"},
                    assistant_msg,
                    {"role": "tool", "tool_call_id": tc.id, "content": '{"temperature": 22, "condition": "sunny"}'},
                ],
                stream=True,
                max_tokens=100,
                temperature=0.0,
                tools=[tool_def],
            )
        )
        content = "".join(c.choices[0].delta.content for c in chunks2 if c.choices[0].delta.content)
        self.assertTrue(
            "22" in content.lower() or "sunny" in content.lower(),
            f"Expected model to reference tool result, got: {content}",
        )