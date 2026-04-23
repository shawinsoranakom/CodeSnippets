def split_text(self, text: str) -> list[Document]:
        """Split markdown file.

        Args:
            text: Markdown file

        Returns:
            List of `Document` objects.
        """
        # Split the input text by newline character ("\n").
        lines = text.split("\n")

        # Final output
        lines_with_metadata: list[LineType] = []

        # Content and metadata of the chunk currently being processed
        current_content: list[str] = []

        current_metadata: dict[str, str] = {}

        # Keep track of the nested header structure
        header_stack: list[HeaderType] = []

        initial_metadata: dict[str, str] = {}

        in_code_block = False

        opening_fence = ""

        for line in lines:
            stripped_line = line.strip()
            # Remove all non-printable characters from the string, keeping only visible
            # text.
            stripped_line = "".join(filter(str.isprintable, stripped_line))
            if not in_code_block:
                # Exclude inline code spans
                if stripped_line.startswith("```") and stripped_line.count("```") == 1:
                    in_code_block = True
                    opening_fence = "```"
                elif stripped_line.startswith("~~~"):
                    in_code_block = True
                    opening_fence = "~~~"
            elif stripped_line.startswith(opening_fence):
                in_code_block = False
                opening_fence = ""

            if in_code_block:
                current_content.append(stripped_line)
                continue

            # Check each line against each of the header types (e.g., #, ##)
            for sep, name in self.headers_to_split_on:
                is_standard_header = stripped_line.startswith(sep) and (
                    # Header with no text OR header is followed by space
                    # Both are valid conditions that sep is being used a header
                    len(stripped_line) == len(sep) or stripped_line[len(sep)] == " "
                )
                is_custom_header = self._is_custom_header(stripped_line, sep)

                # Check if line matches either standard or custom header pattern
                if is_standard_header or is_custom_header:
                    # Ensure we are tracking the header as metadata
                    if name is not None:
                        # Get the current header level
                        if sep in self.custom_header_patterns:
                            current_header_level = self.custom_header_patterns[sep]
                        else:
                            current_header_level = sep.count("#")

                        # Pop out headers of lower or same level from the stack
                        while (
                            header_stack
                            and header_stack[-1]["level"] >= current_header_level
                        ):
                            # We have encountered a new header
                            # at the same or higher level
                            popped_header = header_stack.pop()
                            # Clear the metadata for the
                            # popped header in initial_metadata
                            if popped_header["name"] in initial_metadata:
                                initial_metadata.pop(popped_header["name"])

                        # Push the current header to the stack
                        # Extract header text based on header type
                        if is_custom_header:
                            # For custom headers like **Header**, extract text
                            # between patterns
                            header_text = stripped_line[len(sep) : -len(sep)].strip()
                        else:
                            # For standard headers like # Header, extract text
                            # after the separator
                            header_text = stripped_line[len(sep) :].strip()

                        header: HeaderType = {
                            "level": current_header_level,
                            "name": name,
                            "data": header_text,
                        }
                        header_stack.append(header)
                        # Update initial_metadata with the current header
                        initial_metadata[name] = header["data"]

                    # Add the previous line to the lines_with_metadata
                    # only if current_content is not empty
                    if current_content:
                        lines_with_metadata.append(
                            {
                                "content": "\n".join(current_content),
                                "metadata": current_metadata.copy(),
                            }
                        )
                        current_content.clear()

                    if not self.strip_headers:
                        current_content.append(stripped_line)

                    break
            else:
                if stripped_line:
                    current_content.append(stripped_line)
                elif current_content:
                    lines_with_metadata.append(
                        {
                            "content": "\n".join(current_content),
                            "metadata": current_metadata.copy(),
                        }
                    )
                    current_content.clear()

            current_metadata = initial_metadata.copy()

        if current_content:
            lines_with_metadata.append(
                {
                    "content": "\n".join(current_content),
                    "metadata": current_metadata,
                }
            )

        # lines_with_metadata has each line with associated header metadata
        # aggregate these into chunks based on common metadata
        if not self.return_each_line:
            return self.aggregate_lines_to_chunks(lines_with_metadata)
        return [
            Document(page_content=chunk["content"], metadata=chunk["metadata"])
            for chunk in lines_with_metadata
        ]