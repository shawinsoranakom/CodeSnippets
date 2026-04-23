def extract_tool_calls_streaming(
        self,
        previous_text: str,
        current_text: str,
        delta_text: str,
        previous_token_ids: Sequence[int],
        current_token_ids: Sequence[int],
        delta_token_ids: Sequence[int],
        request: ChatCompletionRequest,
    ) -> DeltaMessage | None:
        if "<|action_start|>" not in current_text:
            self.position = len(current_text)
            return DeltaMessage(content=delta_text)
        # if the tool call is sent, return an empty delta message
        # to make sure the finish_reason will be sent correctly.
        if self.current_tool_id > 0:
            return DeltaMessage(content="")

        last_pos = self.position
        if "<|action_start|><|plugin|>" not in current_text[last_pos:]:
            return None

        new_delta = current_text[last_pos:]
        text, action = new_delta.split("<|action_start|><|plugin|>")

        if len(text) > 0:
            self.position = self.position + len(text)
            return DeltaMessage(content=text)

        action = action.strip()
        action = action.split("<|action_end|>".strip())[0]

        # bit mask flags for partial JSON parsing. If the name hasn't been
        # sent yet, don't allow sending
        # an incomplete string since OpenAI only ever (as far as I have
        # seen) allows sending the entire tool/ function name at once.
        flags = Allow.ALL if self.current_tool_name_sent else Allow.ALL & ~Allow.STR

        try:
            parsable_arr = action

            # tool calls are generated in an object in internlm2
            # it's not support parallel tool calls
            try:
                tool_call_arr: dict = partial_json_parser.loads(parsable_arr, flags)
            except partial_json_parser.core.exceptions.MalformedJSON:
                logger.debug("not enough tokens to parse into JSON yet")
                return None

            # if the current tool name hasn't been sent, send if available
            # - otherwise send nothing
            if not self.current_tool_name_sent:
                function_name = tool_call_arr.get("name")
                if function_name:
                    self.current_tool_id = self.current_tool_id + 1
                    delta = DeltaMessage(
                        tool_calls=[
                            DeltaToolCall(
                                index=self.current_tool_id,
                                type="function",
                                id=make_tool_call_id(),
                                function=DeltaFunctionCall(
                                    name=function_name
                                ).model_dump(exclude_none=True),
                            )
                        ]
                    )
                    self.current_tool_name_sent = True
                    self.streamed_args_for_tool.append("")
                else:
                    delta = None
            # now we know we're on the same tool call and we're streaming
            # arguments
            else:
                prev_arguments = self.get_arguments(
                    self.prev_tool_call_arr[self.current_tool_id]
                )
                cur_arguments = self.get_arguments(tool_call_arr)

                # not arguments generated
                if not cur_arguments and not prev_arguments:
                    delta = None
                # will never happen
                elif not cur_arguments and prev_arguments:
                    logger.error(
                        "INVARIANT - impossible to have arguments reset mid-arguments"
                    )
                    delta = None
                # first time to get parameters
                elif cur_arguments and not prev_arguments:
                    cur_arguments_json = json.dumps(cur_arguments, ensure_ascii=False)

                    arguments_delta = cur_arguments_json[
                        : cur_arguments_json.index(delta_text) + len(delta_text)
                    ]
                    delta = DeltaMessage(
                        tool_calls=[
                            DeltaToolCall(
                                index=self.current_tool_id,
                                function=DeltaFunctionCall(
                                    arguments=arguments_delta
                                ).model_dump(exclude_none=True),
                            )
                        ]
                    )
                    self.streamed_args_for_tool[self.current_tool_id] += arguments_delta
                # both prev and cur parameters, send the increase parameters
                elif cur_arguments and prev_arguments:
                    cur_args_json = json.dumps(cur_arguments, ensure_ascii=False)
                    prev_args_json = json.dumps(prev_arguments, ensure_ascii=False)

                    argument_diff = extract_intermediate_diff(
                        cur_args_json, prev_args_json
                    )

                    delta = DeltaMessage(
                        tool_calls=[
                            DeltaToolCall(
                                index=self.current_tool_id,
                                function=DeltaFunctionCall(
                                    arguments=argument_diff
                                ).model_dump(exclude_none=True),
                            )
                        ]
                    )
                    self.streamed_args_for_tool[self.current_tool_id] += argument_diff

            # check to see if the name is defined and has been sent. if so,
            # stream the name - otherwise keep waiting
            # finish by setting old and returning None as base case
            tool_call_arr["arguments"] = self.get_arguments(tool_call_arr)
            self.prev_tool_call_arr = [tool_call_arr]
            return delta
        except Exception:
            logger.exception("Error trying to handle streaming tool call.")
            logger.debug(
                "Skipping chunk as a result of tool streaming extraction error"
            )
            return None