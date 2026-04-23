def _process_complete_xml_elements(self) -> bool:
        """
        Process complete XML elements in buffer

        Returns:
            bool: Whether complete elements were found and processed
        """
        found_any = False

        while self.last_processed_pos < len(self.streaming_buffer):
            # Find next complete xml element
            element, end_pos = self._find_next_complete_element(self.last_processed_pos)
            if element is None:
                # No complete element found, wait for more data
                break

            # Check if this element should be skipped
            if self._should_skip_element(element):
                self.last_processed_pos = end_pos
                continue

            # Found complete XML element, process it
            try:
                preprocessed_element = self._preprocess_xml_chunk(element)
                # Check if this is the first tool_call start
                if (
                    (
                        preprocessed_element.strip().startswith("<tool_call>")
                        or preprocessed_element.strip().startswith("<function name=")
                    )
                    and self.tool_call_index == 0
                ) and self.text_content_buffer:
                    # First tool_call starts,
                    # output previously collected text content first
                    text_delta = DeltaMessage(content=self.text_content_buffer)
                    self._emit_delta(text_delta)
                    # Clear buffer for potential subsequent text content
                    self.text_content_buffer = ""

                # If a new tool_call starts and
                # there are already completed tool_calls
                if (
                    preprocessed_element.strip().startswith("<tool_call>")
                    and self.tool_call_index > 0
                    and self.current_call_id
                ):
                    # Reset parser state but preserve generated deltas
                    if self.current_param_name:
                        self._end_element("parameter")
                    if self.current_function_open or self.current_function_name:
                        self._end_element("function")
                    # Output final tool_call tail delta
                    final_delta = DeltaMessage(
                        role=None,
                        content=None,
                        reasoning=None,
                        tool_calls=[
                            DeltaToolCall(
                                index=self.tool_call_index - 1,
                                id=self.current_call_id,
                                type="function",
                                function=DeltaFunctionCall(name=None, arguments=""),
                            )
                        ],
                    )
                    self._emit_delta(final_delta)
                    # Reset XML parser and current call state
                    self._reset_xml_parser_after_tool_call()
                # Parse preprocessed element
                self.parser.Parse(preprocessed_element, False)
                found_any = True

            except Exception as e:
                logger.warning("Error when parsing XML elements: %s", e)

            # Update processed position
            self.last_processed_pos = end_pos

        return found_any