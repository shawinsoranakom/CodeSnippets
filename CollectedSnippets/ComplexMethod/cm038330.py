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
        # if the tool call token is not in the tokens generated so far, append
        # output to contents since it's not a tool
        if self.tool_calls_start_token not in current_text:
            return DeltaMessage(content=delta_text)

        # if the tool call token ID IS in the tokens generated so far, that
        # means we're parsing as tool calls now

        # handle if we detected the start of tool calls token which means
        # the start of tool calling
        if (
            self.tool_calls_start_token_id in delta_token_ids
            and len(delta_token_ids) == 1
        ):
            # if it's the only token, return None, so we don't send a chat
            # completion and don't send a control token
            return None

        # bit mask flags for partial JSON parsing. If the name hasn't been
        # sent yet, don't allow sending
        # an incomplete string since OpenAI only ever (as far as I have
        # seen) allows sending the entire tool/ function name at once.
        flags = Allow.ALL if self.current_tool_name_sent else Allow.ALL & ~Allow.STR
        try:
            # Extract the tool calls between the special tool call tokens
            parsable_arr = current_text.split(self.tool_calls_start_token)[-1].split(
                self.tool_calls_end_token
            )[0]

            # tool calls are generated in an array, so do partial JSON
            # parsing on the entire array
            try:
                tool_call_arr: list[dict] = partial_json_parser.loads(
                    parsable_arr, flags
                )
            except partial_json_parser.core.exceptions.MalformedJSON:
                logger.debug("not enough tokens to parse into JSON yet")
                return None

            # select as the current tool call the one we're on the state at

            current_tool_call: dict = (
                tool_call_arr[self.current_tool_id] if len(tool_call_arr) > 0 else {}
            )

            # case -- if no tokens have been streamed for the tool, e.g.
            #   only the array brackets, stream nothing
            if len(tool_call_arr) == 0:
                return None

            # case: we are starting a new tool in the array
            #   -> array has > 0 length AND length has moved past cursor
            elif (
                len(tool_call_arr) > 0 and len(tool_call_arr) > self.current_tool_id + 1
            ):
                # if we're moving on to a new call, first make sure we
                # haven't missed anything in the previous one that was
                # auto-generated due to JSON completions, but wasn't
                # streamed to the client yet.
                if self.current_tool_id >= 0:
                    diff: str | None = current_tool_call.get("arguments")

                    if diff:
                        diff = json.dumps(diff, ensure_ascii=False).replace(
                            self.streamed_args_for_tool[self.current_tool_id], ""
                        )
                        delta = DeltaMessage(
                            tool_calls=[
                                DeltaToolCall(
                                    index=self.current_tool_id,
                                    function=DeltaFunctionCall(
                                        arguments=diff
                                    ).model_dump(exclude_none=True),
                                )
                            ]
                        )
                        self.streamed_args_for_tool[self.current_tool_id] += diff
                    else:
                        delta = None
                else:
                    delta = None
                # re-set stuff pertaining to progress in the current tool
                self.current_tool_id = len(tool_call_arr) - 1
                self.current_tool_name_sent = False
                self.streamed_args_for_tool.append("")
                logger.debug("starting on new tool %d", self.current_tool_id)
                return delta

            # case: update an existing tool - this is handled below

            # if the current tool name hasn't been sent, send if available
            # - otherwise send nothing
            if not self.current_tool_name_sent:
                function_name = current_tool_call.get("name")
                if function_name:
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
                else:
                    delta = None

            # now we know we're on the same tool call and we're streaming
            # arguments
            else:
                prev_arguments = self.prev_tool_call_arr[self.current_tool_id].get(
                    "arguments"
                )
                cur_arguments = current_tool_call.get("arguments")

                new_text = delta_text.replace("'", '"')

                if not cur_arguments and not prev_arguments:
                    delta = None
                elif not cur_arguments and prev_arguments:
                    logger.error(
                        "INVARIANT - impossible to have arguments reset mid-arguments"
                    )
                    delta = None
                elif cur_arguments and not prev_arguments:
                    cur_arguments_json = json.dumps(cur_arguments, ensure_ascii=False)
                    logger.debug("finding %s in %s", new_text, cur_arguments_json)

                    arguments_delta = cur_arguments_json[
                        : cur_arguments_json.index(new_text) + len(new_text)
                    ]
                    logger.debug(
                        "First tokens in arguments received: %s", arguments_delta
                    )
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

                elif cur_arguments and prev_arguments:
                    cur_args_json = json.dumps(cur_arguments, ensure_ascii=False)
                    prev_args_json = json.dumps(prev_arguments, ensure_ascii=False)
                    logger.debug(
                        "Searching for diff between \n%s\n%s",
                        cur_args_json,
                        prev_args_json,
                    )

                    argument_diff = extract_intermediate_diff(
                        cur_args_json, prev_args_json
                    )
                    logger.debug("got arguments diff: %s", argument_diff)
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
                else:
                    # try parsing it with regular JSON - if it works we're
                    # at the end, and we need to send the difference between
                    # tokens streamed so far and the valid JSON
                    delta = None

            # check to see if the name is defined and has been sent. if so,
            # stream the name - otherwise keep waiting
            # finish by setting old and returning None as base case
            self.prev_tool_call_arr = tool_call_arr
            return delta

        except Exception:
            logger.exception("Error trying to handle streaming tool call.")
            logger.debug(
                "Skipping chunk as a result of tool streaming extraction error"
            )
            return None