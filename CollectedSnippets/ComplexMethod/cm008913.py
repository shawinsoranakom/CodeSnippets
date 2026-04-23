def split_text(self, text: str) -> list[Document]:
        """Split the input text into structured chunks.

        This method processes the input text line by line, identifying and handling
        specific patterns such as headers, code blocks, and horizontal rules to split it
        into structured chunks based on headers, code blocks, and horizontal rules.

        Args:
            text: The input text to be split into chunks.

        Returns:
            A list of `Document` objects representing the structured
            chunks of the input text. If `return_each_line` is enabled, each line
            is returned as a separate `Document`.
        """
        # Reset the state for each new file processed
        self.chunks.clear()
        self.current_chunk = Document(page_content="")
        self.current_header_stack.clear()

        raw_lines = text.splitlines(keepends=True)

        while raw_lines:
            raw_line = raw_lines.pop(0)
            header_match = self._match_header(raw_line)
            code_match = self._match_code(raw_line)
            horz_match = self._match_horz(raw_line)
            if header_match:
                self._complete_chunk_doc()

                if not self.strip_headers:
                    self.current_chunk.page_content += raw_line

                # add the header to the stack
                header_depth = len(header_match.group(1))
                header_text = header_match.group(2)
                self._resolve_header_stack(header_depth, header_text)
            elif code_match:
                self._complete_chunk_doc()
                self.current_chunk.page_content = self._resolve_code_chunk(
                    raw_line, raw_lines
                )
                self.current_chunk.metadata["Code"] = code_match.group(1)
                self._complete_chunk_doc()
            elif horz_match:
                self._complete_chunk_doc()
            else:
                self.current_chunk.page_content += raw_line

        self._complete_chunk_doc()
        # I don't see why `return_each_line` is a necessary feature of this splitter.
        # It's easy enough to do outside of the class and the caller can have more
        # control over it.
        if self.return_each_line:
            return [
                Document(page_content=line, metadata=chunk.metadata)
                for chunk in self.chunks
                for line in chunk.page_content.splitlines()
                if line and not line.isspace()
            ]
        return self.chunks