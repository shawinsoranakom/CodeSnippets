def _start_element(self, name: str, attrs: dict[str, str]):
        """Handle XML start element events"""

        if name == "root":
            return

        if name == "tool_call":
            # Before opening new tool_call,
            # automatically complete previous unclosed tags
            self._auto_close_open_parameter_if_needed("tool_call")

            self.parameters = {}
            self.current_call_id = make_tool_call_id()
            self.current_param_is_first = True
            self.tool_call_index += 1
        elif name.startswith("function") or (name == "function"):
            # If missing tool_call, manually complete
            if not self.current_call_id:
                self._start_element("tool_call", {})
            # Before opening new function,
            # automatically complete previous unclosed tags (parameter/function)
            self._auto_close_open_parameter_if_needed("function")
            function_name = self._extract_function_name(name, attrs)
            self.current_function_name = function_name
            self.current_function_open = True
            if function_name:
                delta = DeltaMessage(
                    tool_calls=[
                        DeltaToolCall(
                            index=self.tool_call_index - 1,
                            id=self.current_call_id,
                            type="function",
                            function=DeltaFunctionCall(
                                name=function_name, arguments=""
                            ),
                        )
                    ]
                )
                self._emit_delta(delta)
        elif name.startswith("parameter") or (name == "parameter"):
            # If previous parameter hasn't ended normally,
            # complete its end first, then start new parameter
            self._auto_close_open_parameter_if_needed("parameter")
            param_name = self._extract_parameter_name(name, attrs)
            self.current_param_name = param_name
            self.current_param_value = ""
            self.current_param_value_converted = ""
            self.start_quote_emitted = False  # Reset start quote flag

            # Only output parameter name and colon,
            # don't output quotes
            # decide after parameter value type is determined
            if param_name:
                if not self.parameters:
                    # First parameter
                    # start JSON, only output parameter name and colon
                    json_start = f'{{"{param_name}": '
                    delta = DeltaMessage(
                        tool_calls=[
                            DeltaToolCall(
                                index=self.tool_call_index - 1,
                                id=self.current_call_id,
                                type="function",
                                function=DeltaFunctionCall(
                                    name=None, arguments=json_start
                                ),
                            )
                        ]
                    )
                    self._emit_delta(delta)
                    self.current_param_is_first = True
                else:
                    # Subsequent parameters
                    # add comma and parameter name, no quotes
                    json_continue = f', "{param_name}": '
                    delta = DeltaMessage(
                        tool_calls=[
                            DeltaToolCall(
                                index=self.tool_call_index - 1,
                                id=self.current_call_id,
                                type="function",
                                function=DeltaFunctionCall(
                                    name=None, arguments=json_continue
                                ),
                            )
                        ]
                    )
                    self._emit_delta(delta)
                    self.current_param_is_first = False