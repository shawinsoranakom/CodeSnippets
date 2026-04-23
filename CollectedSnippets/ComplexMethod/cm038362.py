def _find_next_complete_element(self, start_pos: int) -> tuple[str | None, int]:
        """
        Find next complete XML element from specified position

        Args:
            start_pos: Position to start searching

        Returns:
            (Complete element string, element end position),
            returns (None, start_pos) if no complete element found
        """
        buffer = self.streaming_buffer[start_pos:]

        if not buffer:
            return None, start_pos

        if buffer.startswith("<"):
            # Need to ensure no new < appears,
            # find the nearest one between < and >
            tag_end = buffer.find("<", 1)
            tag_end2 = buffer.find(">", 1)
            if tag_end != -1 and tag_end2 != -1:
                # Next nearest is <
                if tag_end < tag_end2:
                    return buffer[:tag_end], start_pos + tag_end
                # Next nearest is >, means found XML element
                else:
                    return buffer[: tag_end2 + 1], start_pos + tag_end2 + 1
            elif tag_end != -1:
                return buffer[:tag_end], start_pos + tag_end
            elif tag_end2 != -1:
                return buffer[: tag_end2 + 1], start_pos + tag_end2 + 1
            else:
                # If currently not parsing tool calls (entering a tool_call),
                # check if starts with <tool_call> or <function=
                if self.current_call_id is None:
                    # Check if might be start of <tool_call>
                    if buffer == "<tool_call>"[: len(buffer)]:
                        # Might be start of <tool_call>, wait for more data
                        return None, start_pos
                    elif (
                        buffer.startswith("<function=")
                        or buffer == "<function="[: len(buffer)]
                    ):
                        # Might be start of <function=, wait for more data
                        # to get the complete function tag
                        return None, start_pos
                    else:
                        # Not start of <tool_call> or <function=, treat as text
                        return buffer, start_pos + len(buffer)
                else:
                    # When parsing tool calls,
                    # wait for more data to get complete tag
                    return None, start_pos
        else:
            # Find text content (until next < or buffer end)
            next_tag_pos = buffer.find("<")
            if next_tag_pos != -1:
                # Found text content
                text_content = buffer[:next_tag_pos]
                return text_content, start_pos + next_tag_pos
            else:
                # Buffer end is all text, process
                # (no longer wait for more data)
                remaining = buffer
                return remaining, start_pos + len(remaining)