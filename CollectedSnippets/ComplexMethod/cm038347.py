def _preprocess_xml_chunk(self, chunk: str) -> str:
        """
        Preprocess XML chunk, handle non-standard formats,
        and escape special characters

        Args:
            chunk: Original XML chunk

        Returns:
            Processed XML chunk
        """

        # Check if this is a tool_call related element
        is_tool_call = False
        if chunk.startswith(self.tool_call_start_token) or chunk.startswith(
            self.tool_call_end_token
        ):
            is_tool_call = True
        # Check for function tags (including malformed ones without =)
        # <function=xxx>, </function>, <function xxx>, <functionxxx>
        if (
            chunk.startswith(self.function_start_token)
            or chunk.startswith(self.function_end_token)
            or chunk.startswith("<function ")
            or re.match(r"^<function[a-zA-Z_]", chunk)
        ):  # <functionXXX without space or =
            is_tool_call = True
        if chunk.startswith(self.parameter_start_token) or chunk.startswith(
            self.parameter_end_token
        ):
            is_tool_call = True

        # Fallback: fix incomplete <parameter= or <function= tags without
        # closing >
        # This handles cases like: <parameter=-C:\n or <parameter=-B 5\n
        # Apply when parsing tool calls OR when chunk looks like a function/
        # parameter tag
        if (
            self.current_call_id is not None
            or chunk.startswith("<function")
            or chunk.startswith("<parameter")
        ):
            chunk = self._fix_incomplete_tag_in_chunk(chunk)

        # Handle <function=name> format -> <function name="name">
        processed = re.sub(r"<function=([^>]+)>", r'<function name="\1">', chunk)
        # Handle <parameter=name> format -> <parameter name="name">
        processed = re.sub(r"<parameter=([^>]+)>", r'<parameter name="\1">', processed)

        original_chunk = chunk
        # If in parameter value accumulation mode
        if self._pre_inside_parameter:
            # Parameter end: output accumulated raw text
            # safely then return </parameter>
            if processed.startswith("</parameter>"):
                body_text = self._pre_param_buffer
                # Trigger deferred parsing mode
                # literal_eval+json output in end_element
                self.defer_current_parameter = True
                self.deferred_param_raw_value = body_text
                # Clean up state
                self._pre_inside_parameter = False
                self._pre_param_buffer = ""
                self._pre_current_param_name = None
                safe_text = self._escape_xml_special_chars(body_text)
                return f"{safe_text}</parameter>"
            else:
                # If this is the first block of content after entering parameter
                # evaluate if deferred parsing is needed;
                # If not needed, exit accumulation mode
                # and pass through directly
                if self._pre_param_buffer == "":
                    # Get current parameter type
                    param_type = (
                        self._get_param_type(self._pre_current_param_name)
                        if self._pre_current_param_name
                        else "string"
                    )
                    # Only these types need deferred parsing to
                    # handle Python literals containing single quotes
                    is_object_type = param_type in ["object"]
                    is_complex_type = (
                        param_type in ["array", "arr", "sequence"]
                        or param_type.startswith("dict")
                        or param_type.startswith("list")
                    )

                    # Only delay when contains container symbols
                    # and has single quotes and is complex type
                    has_container_hint = (
                        ("[" in original_chunk)
                        or ("{" in original_chunk)
                        or ("(" in original_chunk)
                    )

                    # Determine if deferred parsing is needed
                    need_defer = False
                    if is_complex_type:
                        # Complex type, always need deferred parsing
                        need_defer = True
                    elif (
                        is_object_type
                        and has_container_hint
                        and ("'" in original_chunk)
                    ):
                        # Object type with container symbols
                        # and single quotes, need deferred parsing
                        need_defer = True

                    if not need_defer:
                        # No need for deferred parsing,
                        # exit parameter mode directly
                        self._pre_inside_parameter = False
                        return self._escape_xml_special_chars(original_chunk)
                self._pre_param_buffer += original_chunk
                return ""

        # Parameter start: enable accumulation
        if processed.startswith("<parameter name="):
            m = re.match(r'<parameter name="([^"]+)">', processed)
            if m:
                self._pre_current_param_name = m.group(1)
            self._pre_inside_parameter = True
            self._pre_param_buffer = ""
            return processed

        # If processed doesn't contain special_token, escape processed
        # This is because XML parsing encounters special characters
        # and reports errors, so escaping is needed
        if not is_tool_call:
            processed = self._escape_xml_special_chars(processed)
        return processed