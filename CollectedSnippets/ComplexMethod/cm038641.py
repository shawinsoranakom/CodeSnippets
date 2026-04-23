def _construct_input_messages_with_harmony(
        self,
        request: ResponsesRequest,
        prev_response: ResponsesResponse | None,
    ) -> list[OpenAIHarmonyMessage]:
        messages: list[OpenAIHarmonyMessage] = []
        if prev_response is None:
            # New conversation.
            tool_types = extract_tool_types(request.tools)
            with_custom_tools = has_custom_tools(tool_types)

            sys_msg = self._construct_harmony_system_input_message(
                request, with_custom_tools, tool_types
            )
            messages.append(sys_msg)
            if with_custom_tools:
                dev_msg = get_developer_message(
                    instructions=request.instructions, tools=request.tools
                )
                messages.append(dev_msg)
            messages += construct_harmony_previous_input_messages(request)

        else:
            # Continue the previous conversation.
            # FIXME(woosuk): Currently, request params like reasoning and
            # instructions are ignored.
            prev_msgs = self.msg_store[prev_response.id]

            # FIXME(woosuk): The slice-delete-reappend cycle below is
            # currently a no-op --- it removes messages then puts them all
            # back unfiltered. It may be intentionally deferred (see FIXME
            # above) or redundant if the Harmony encoder already strips
            # analysis messages at render time. If analysis messages need
            # to be dropped here, add a channel != "analysis" filter when
            # re-appending, similar to auto_drop_analysis_messages in
            # harmony_utils.py.
            if len(prev_msgs) > 0:
                last_msg = prev_msgs[-1]
                assert isinstance(last_msg, OpenAIHarmonyMessage)
                if last_msg.channel == "final":
                    prev_final_msg_idx = -1
                    for i in range(len(prev_msgs) - 2, -1, -1):
                        prev_msg_i = prev_msgs[i]
                        assert isinstance(prev_msg_i, OpenAIHarmonyMessage)
                        if prev_msg_i.channel == "final":
                            prev_final_msg_idx = i
                            break
                    recent_turn_msgs = prev_msgs[prev_final_msg_idx + 1 :]
                    del prev_msgs[prev_final_msg_idx + 1 :]
                    for msg in recent_turn_msgs:
                        assert isinstance(msg, OpenAIHarmonyMessage)
                        prev_msgs.append(msg)
            messages.extend(prev_msgs)
        # Append the new input.
        # Responses API supports simple text inputs without chat format.
        if isinstance(request.input, str):
            # Skip empty string input when previous_input_messages supplies
            # the full conversation history --- an empty trailing user message
            # confuses the model into thinking nothing was sent.
            if request.input or not request.previous_input_messages:
                messages.append(get_user_message(request.input))
        else:
            if prev_response is not None:
                prev_outputs = copy(prev_response.output)
            else:
                prev_outputs = []
            for response_msg in request.input:
                new_msg = response_input_to_harmony(response_msg, prev_outputs)
                if new_msg is not None and new_msg.author.role != "system":
                    messages.append(new_msg)

                # User passes in a tool call request and its output. We need
                # to add the tool call request to prev_outputs so that
                # response_input_to_harmony can find the tool call request when
                # parsing the tool call output.
                if isinstance(response_msg, ResponseFunctionToolCall):
                    prev_outputs.append(response_msg)
        return messages