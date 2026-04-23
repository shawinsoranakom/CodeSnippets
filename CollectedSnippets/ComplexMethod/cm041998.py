def _edit_impl(lines, start, end, content):
        """Internal method to handle editing a file.

        REQUIRES (should be checked by caller):
            start <= end
            start and end are between 1 and len(lines) (inclusive)
            content ends with a newline

        Args:
            lines: list[str]: The lines in the original file.
            start: int: The start line number for editing.
            end: int: The end line number for editing.
            content: str: The content to replace the lines with.

        Returns:
            content: str: The new content of the file.
            n_added_lines: int: The number of lines added to the file.
        """
        # Handle cases where start or end are None
        if start is None:
            start = 1  # Default to the beginning
        if end is None:
            end = len(lines)  # Default to the end
        # Check arguments
        if not (1 <= start <= len(lines)):
            raise LineNumberError(
                f"Invalid start line number: {start}. Line numbers must be between 1 and {len(lines)} (inclusive)."
            )
        if not (1 <= end <= len(lines)):
            raise LineNumberError(
                f"Invalid end line number: {end}. Line numbers must be between 1 and {len(lines)} (inclusive)."
            )
        if start > end:
            raise LineNumberError(f"Invalid line range: {start}-{end}. Start must be less than or equal to end.")

        # Split content into lines and ensure it ends with a newline
        if not content.endswith("\n"):
            content += "\n"
        content_lines = content.splitlines(True)

        # Calculate the number of lines to be added
        n_added_lines = len(content_lines)

        # Remove the specified range of lines and insert the new content
        new_lines = lines[: start - 1] + content_lines + lines[end:]

        # Handle the case where the original lines are empty
        if len(lines) == 0:
            new_lines = content_lines

        # Join the lines to create the new content
        content = "".join(new_lines)
        return content, n_added_lines