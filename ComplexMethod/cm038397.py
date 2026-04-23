def _build_args_json_so_far(
        self,
        tool_name: str,
        inner_text: str,
        is_complete: bool,
    ) -> str:
        """Build the JSON arguments string from the XML pairs seen so far.

        For complete ``<arg_key>/<arg_value>`` pairs the value is fully
        formatted.  For the last argument whose ``<arg_value>`` has been
        opened but not closed, the partial string content is included
        (JSON-escaped, with an opening ``"`` but no closing ``"``).

        The closing ``}`` is only appended when ``is_complete`` is True
        (i.e. the ``</tool_call>`` tag has arrived).
        """
        # Find all complete arg pairs
        pairs = self.func_arg_regex.findall(inner_text)

        parts: list[str] = []
        for key, value in pairs:
            key = key.strip()
            key_json = json.dumps(key, ensure_ascii=False)
            if self._is_string_type(tool_name, key, self.tools):
                # Don't strip string values — whitespace is significant
                # and must match the partial-value path for diffing.
                val_json = json.dumps(value, ensure_ascii=False)
            else:
                val_json = json.dumps(
                    self._deserialize(value.strip()), ensure_ascii=False
                )
            parts.append(f"{key_json}: {val_json}")

        # Check for a partial (incomplete) arg value
        # Find the last <arg_value> that isn't closed
        last_val_start = inner_text.rfind(self.arg_val_start)
        last_val_end = inner_text.rfind(self.arg_val_end)
        has_partial_value = last_val_start != -1 and (
            last_val_end == -1 or last_val_end < last_val_start
        )

        if has_partial_value:
            # Find the key for this partial value
            # Look for the last <arg_key>...</arg_key> before this <arg_value>
            last_key_match = None
            for m in self._arg_key_pattern.finditer(inner_text[:last_val_start]):
                last_key_match = m

            if last_key_match:
                partial_key = last_key_match.group(1).strip()
                partial_content_start = last_val_start + len(self.arg_val_start)
                partial_content = inner_text[partial_content_start:]

                # Hold back any partial </arg_value> suffix
                overlap = partial_tag_overlap(partial_content, self.arg_val_end)
                if overlap:
                    partial_content = partial_content[:-overlap]

                key_json = json.dumps(partial_key, ensure_ascii=False)
                if is_complete:
                    # Tool call finished but </arg_value> is missing
                    # (malformed output). Treat partial as complete value
                    # so the diff naturally closes any open quotes.
                    if self._is_string_type(tool_name, partial_key, self.tools):
                        val_json = json.dumps(partial_content, ensure_ascii=False)
                    else:
                        val_json = json.dumps(
                            self._deserialize(partial_content.strip()),
                            ensure_ascii=False,
                        )
                    parts.append(f"{key_json}: {val_json}")
                elif self._is_string_type(tool_name, partial_key, self.tools):
                    escaped = self._json_escape_string_content(partial_content)
                    # Open quote but no close — more content may arrive
                    parts.append(f'{key_json}: "{escaped}')
                else:
                    # Non-string partial: include raw content, no wrapping
                    parts.append(f"{key_json}: {partial_content}")

        if not parts:
            return "{}" if is_complete else ""

        joined = "{" + ", ".join(parts)
        if is_complete:
            joined += "}"
        return joined