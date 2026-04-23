def test_responses_multi_turn_streaming(self):
        tool_def = self._get_tool_def()

        # Turn 1: streaming — get completed response with tool calls
        events = list(
            self.client.responses.create(
                model=self.MODEL,
                input="What is the weather in Paris?",
                stream=True,
                max_output_tokens=50,
                tools=[tool_def],
            )
        )
        completed = [e for e in events if e.type == "response.completed"]
        self.assertEqual(len(completed), 1)
        resp1_output = completed[0].response.output
        fc_items = [o for o in resp1_output if o.type == "function_call"]
        self.assertGreater(len(fc_items), 0)

        # Turn 2: streaming — send back tool result
        input_list = [{"role": "user", "content": "What is the weather in Paris?"}]
        input_list += resp1_output
        input_list.append(
            {
                "type": "function_call_output",
                "call_id": fc_items[0].call_id,
                "output": '{"temperature": 22, "condition": "sunny"}',
            }
        )
        events2 = list(
            self.client.responses.create(
                model=self.MODEL,
                input=input_list,
                stream=True,
                max_output_tokens=100,
                tools=[tool_def],
            )
        )
        content = "".join(e.delta for e in events2 if e.type == "response.output_text.delta")
        self.assertTrue(
            "22" in content.lower() or "sunny" in content.lower(),
            f"Expected model to reference tool result, got: {content}",
        )