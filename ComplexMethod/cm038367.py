def _end_element(self, name: str):
        """Handle XML end element events"""

        if name == "root":
            return

        # If function or tool_call ends and there are still unclosed parameters,
        # complete parameter end first
        if (
            name.startswith("function") or name == "function" or name == "tool_call"
        ) and self.current_param_name:
            self._auto_close_open_parameter_if_needed()

        if (
            name.startswith("parameter") or name == "parameter"
        ) and self.current_param_name:
            # End current parameter
            param_name = self.current_param_name
            param_value = self.current_param_value

            # If in deferred parsing mode,
            # perform overall parsing on raw content
            # accumulated in preprocessing stage and output once
            if self.defer_current_parameter:
                raw_text = (
                    self.deferred_param_raw_value
                    if self.deferred_param_raw_value
                    else param_value
                )
                parsed_value = None
                output_arguments = None
                try:
                    # If previously delayed trailing newline,
                    # add it back before parsing
                    if self.should_emit_end_newline:
                        raw_for_parse = raw_text + "\n"
                    else:
                        raw_for_parse = raw_text
                    parsed_value = ast.literal_eval(raw_for_parse)
                    output_arguments = json.dumps(parsed_value, ensure_ascii=False)
                except Exception:
                    # Fallback: output as string as-is
                    output_arguments = json.dumps(raw_text, ensure_ascii=False)
                    parsed_value = raw_text

                delta = DeltaMessage(
                    tool_calls=[
                        DeltaToolCall(
                            index=self.tool_call_index - 1,
                            id=self.current_call_id,
                            type="function",
                            function=DeltaFunctionCall(
                                name=None, arguments=output_arguments
                            ),
                        )
                    ]
                )
                self._emit_delta(delta)

                # Clean up and store
                self.should_emit_end_newline = False
                self.parameters[param_name] = parsed_value
                self.current_param_name = None
                self.current_param_value = ""
                self.current_param_value_converted = ""
                self.start_quote_emitted = False
                self.defer_current_parameter = False
                self.deferred_param_raw_value = ""
                return

            param_type = self._get_param_type(param_name)

            # convert complete parameter value by param_type
            converted_value = self._convert_param_value(param_value, param_type)

            # Decide whether to add end quote based on parameter type
            if param_type in ["string", "str", "text", "varchar", "char", "enum"]:
                # For empty string parameters, need special handling
                if not param_value and not self.start_quote_emitted:
                    # No start quote output,
                    # directly output complete empty string
                    delta = DeltaMessage(
                        tool_calls=[
                            DeltaToolCall(
                                index=self.tool_call_index - 1,
                                id=self.current_call_id,
                                type="function",
                                function=DeltaFunctionCall(name=None, arguments='""'),
                            )
                        ]
                    )
                    self._emit_delta(delta)
                else:
                    # Non-empty parameter value, output end quote
                    delta = DeltaMessage(
                        tool_calls=[
                            DeltaToolCall(
                                index=self.tool_call_index - 1,
                                id=self.current_call_id,
                                type="function",
                                function=DeltaFunctionCall(name=None, arguments='"'),
                            )
                        ]
                    )
                    self._emit_delta(delta)

            self.should_emit_end_newline = False
            # Store converted value
            self.parameters[param_name] = converted_value
            self.current_param_name = None
            self.current_param_value = ""
            self.current_param_value_converted = ""
            self.start_quote_emitted = False

        elif name.startswith("function") or name == "function":
            # if there are parameters, close JSON object
            if self.parameters:
                delta = DeltaMessage(
                    tool_calls=[
                        DeltaToolCall(
                            index=self.tool_call_index - 1,
                            id=self.current_call_id,
                            type="function",
                            function=DeltaFunctionCall(name=None, arguments="}"),
                        )
                    ]
                )
                self._emit_delta(delta)
            # return empty object
            else:
                delta = DeltaMessage(
                    tool_calls=[
                        DeltaToolCall(
                            index=self.tool_call_index - 1,
                            id=self.current_call_id,
                            type="function",
                            function=DeltaFunctionCall(name=None, arguments="{}"),
                        )
                    ]
                )
                self._emit_delta(delta)
            self.current_function_open = False

        elif name == "tool_call":
            # Before ending tool_call,
            # ensure function is closed to complete missing right brace
            if self.current_function_open:
                # If there are still unclosed parameters, close them first
                if self.current_param_name:
                    self._end_element("parameter")
                # Close function, ensure output '}' or '{}'
                self._end_element("function")
            # Final Delta
            delta = DeltaMessage(
                tool_calls=[
                    DeltaToolCall(
                        index=self.tool_call_index - 1,
                        id=self.current_call_id,
                        type="function",
                        function=DeltaFunctionCall(name=None, arguments=""),
                    )
                ]
            )
            self._emit_delta(delta)

            # Check if there's text content to output (between tool_calls)
            if self.text_content_buffer.strip():
                text_delta = DeltaMessage(content=self.text_content_buffer)
                self._emit_delta(text_delta)

            self._reset_xml_parser_after_tool_call()