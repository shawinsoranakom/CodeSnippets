def _process_buffer(self, new_content: str) -> str:
        """
        Process buffered content and return output content.

        Args:
            new_content: New content to add to buffer

        Returns:
            Processed output content
        """
        self.pending_buffer += new_content
        output_content = ""

        if self.in_thinking_tag:
            output_content = self.pending_buffer
            self.pending_buffer = ""
            return output_content

        while self.pending_buffer:
            start_pos = self.pending_buffer.find(self.tool_call_start_token)
            end_pos = self.pending_buffer.find(self.tool_call_end_token)

            if start_pos != -1 and (end_pos == -1 or start_pos < end_pos):
                tag_pos, tag_len = start_pos, len(self.tool_call_start_token)
            elif end_pos != -1:
                tag_pos, tag_len = end_pos, len(self.tool_call_end_token)
            else:
                if self._is_potential_tag_start(self.pending_buffer):
                    break
                output_content += self.pending_buffer
                self.pending_buffer = ""
                break

            output_content += self.pending_buffer[:tag_pos]
            self.pending_buffer = self.pending_buffer[tag_pos + tag_len :]

        return output_content