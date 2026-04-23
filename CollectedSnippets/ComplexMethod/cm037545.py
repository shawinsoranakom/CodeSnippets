def _get_content_sections(
        self, current_text: str
    ) -> tuple[str | None, int | None, str | None]:
        """Parse the text to extract the reasoning content / content
        if we have them.

        Args:
            current_text (str): The full previous + delta text.

        Returns:
            tuple[Optional[str], Optional[int], Optional[str]]: Tuple of len 3
            containing the reasoning content, the length of the response seq
            (if there is one) and the non-reasoning content.
        """
        current_chunk_start = 0
        start_reasoning = None
        parsed_content = False
        delimiter_idxs = [
            idx
            for idx, char in enumerate(current_text)
            if char == self.seq_boundary_end
        ]

        for current_chunk_end in delimiter_idxs:
            current_chunk = current_text[current_chunk_start:current_chunk_end]
            # Check to see if the start of reasoning seq if complete
            if start_reasoning is None:
                for think_start in self.valid_think_starts:
                    if current_chunk == think_start[:-1]:
                        start_reasoning = current_chunk_end + 1
                        current_chunk_start = current_chunk_end + 1
                        break

            # Check to see if the start of response seq if complete
            elif not parsed_content:
                for response_start in self.valid_response_starts:
                    if current_chunk[-len(response_start) + 1 :] == response_start[:-1]:
                        # Mark end of reasoning and start response content
                        # after the start of response sequence.
                        end_reasoning = current_chunk_end - len(response_start)
                        reasoning = current_text[start_reasoning:end_reasoning]
                        response_content = current_text[current_chunk_end + 1 :]
                        return reasoning, len(response_start), response_content

        if start_reasoning and not parsed_content:
            return current_text[start_reasoning:], None, None
        return None, None, None