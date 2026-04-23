def extract_tool_call_required_streaming(
        self,
        previous_text: str,
        current_text: str | None,
        delta_text: str,
        function_name_returned: bool,
        tool_call_idx: int | None = None,
    ) -> tuple[DeltaMessage | None, bool]:
        if current_text is None or current_text == "":
            # if the current text is empty, we cannot parse it
            return None, function_name_returned
        try:
            flags = Allow.ALL
            obj, _ = partial_json_loads(current_text, flags)
        except (
            partial_json_parser.core.exceptions.MalformedJSON,
            json.JSONDecodeError,
        ):
            logger.debug("not enough tokens to parse into JSON yet")
            obj = None

        # check if the current text is a valid array
        # containing a partial tool calling object
        # if not repeat
        if obj is None or not isinstance(obj, list) or not len(obj) > 0:
            function_name_returned = False
            delta_message = None
        else:
            _, finishes_previous_tool = OpenAIServingChat._filter_delta_text(
                delta_text, previous_text
            )
            # take the last tool call from the generated list
            current_tool_call = obj[-1]

            # once parameters have been generated the name is complete as well
            if not finishes_previous_tool and (
                "name" not in current_tool_call or "parameters" not in current_tool_call
            ):
                function_name_returned = False
                delta_message = None
            else:
                if not function_name_returned:
                    # get partly generated arguments from the latest tool call
                    param_match = re.search(
                        r'.*"parameters":\s*(.*)', current_text, re.DOTALL
                    )
                    arguments = param_match.group(1) if param_match else ""
                    arguments, _ = OpenAIServingChat._filter_delta_text(
                        arguments, previous_text
                    )

                    # if this iteration finishes a previous tool call but a
                    # new incomplete tool is already generated, take the
                    # previous from the list
                    if finishes_previous_tool and "parameters" not in current_tool_call:
                        current_tool_call = obj[-2]

                    function_name_returned = True
                    tool_call_id = make_tool_call_id(
                        id_type=self.tool_call_id_type,
                        func_name=current_tool_call["name"],
                        idx=tool_call_idx,
                    )
                    delta_message = DeltaMessage(
                        tool_calls=[
                            DeltaToolCall(
                                id=tool_call_id,
                                function=DeltaFunctionCall(
                                    name=current_tool_call["name"], arguments=arguments
                                ),
                                index=len(obj) - 1,
                                type="function",
                            )
                        ]
                    )

                else:
                    delta_text, _ = OpenAIServingChat._filter_delta_text(
                        delta_text, previous_text
                    )

                    if delta_text != "":
                        delta_message = DeltaMessage(
                            tool_calls=[
                                DeltaToolCall(
                                    function=DeltaFunctionCall(
                                        # OpenAI API returns None
                                        # instead of name every time
                                        name=None,
                                        arguments=delta_text,
                                    ),
                                    index=len(obj) - 1,
                                )
                            ]
                        )
                    else:
                        delta_message = None

        return delta_message, function_name_returned