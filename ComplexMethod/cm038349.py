def _char_data(self, data: str):
        """Handle XML character data events"""
        if data and self.current_param_name:
            # If preprocessing stage determines deferred parsing is needed,
            # only cache character data, no streaming output
            if self.defer_current_parameter:
                original_data = data
                if self.should_emit_end_newline:
                    original_data = "\n" + original_data
                    self.should_emit_end_newline = False
                if original_data.endswith("\n"):
                    self.should_emit_end_newline = True
                    original_data = original_data[:-1]
                self.current_param_value += original_data
                return

            param_type = self._get_param_type(self.current_param_name)

            # Check if this is the first time receiving data for this parameter
            # If this is the first packet of data and starts with \n, remove \n
            if not self.current_param_value and data.startswith("\n"):
                data = data[1:]

            # Output start quote for string type (if not already output)
            if (
                param_type in ["string", "str", "text", "varchar", "char", "enum"]
                and not self.start_quote_emitted
            ):
                quote_delta = DeltaMessage(
                    tool_calls=[
                        DeltaToolCall(
                            index=self.tool_call_index - 1,
                            id=self.current_call_id,
                            type="function",
                            function=DeltaFunctionCall(name=None, arguments='"'),
                        )
                    ]
                )
                self._emit_delta(quote_delta)
                self.start_quote_emitted = True

            if not data:
                return

            original_data = data
            # Delay output of trailing newline
            if self.should_emit_end_newline:
                original_data = "\n" + original_data
                self.should_emit_end_newline = False
            if original_data.endswith("\n"):
                self.should_emit_end_newline = True
                original_data = original_data[:-1]
            self.current_param_value += original_data

            # convert parameter value by param_type
            converted_value = self._convert_param_value(
                self.current_param_value, param_type
            )
            output_data = self._convert_for_json_streaming(converted_value, param_type)

            delta_data = output_data[len(self.current_param_value_converted) :]
            self.current_param_value_converted = output_data

            delta = DeltaMessage(
                tool_calls=[
                    DeltaToolCall(
                        index=self.tool_call_index - 1,
                        id=self.current_call_id,
                        type="function",
                        function=DeltaFunctionCall(name=None, arguments=delta_data),
                    )
                ]
            )
            self._emit_delta(delta)