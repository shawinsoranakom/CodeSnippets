def _find_tool_boundaries(self, text: str) -> list[tuple[int, int]]:
        """
        Find the boundaries of tool calls in text.

        Args:
            text: Text to analyze

        Returns:
            List of (start, end) positions for tool calls
        """
        boundaries = []
        i = 0
        while i < len(text):
            if text[i] == "{":
                start = i
                depth = 0
                has_name = False
                has_arguments = False

                while i < len(text):
                    if text[i] == "{":
                        depth += 1
                    elif text[i] == "}":
                        depth -= 1
                        if depth == 0:
                            end = i + 1
                            segment = text[start:end]
                            if '"name"' in segment and '"arguments"' in segment:
                                boundaries.append((start, end))
                            break

                    if not has_name and '"name"' in text[start : i + 1]:
                        has_name = True
                    if not has_arguments and '"arguments"' in text[start : i + 1]:
                        has_arguments = True

                    i += 1

                if depth > 0 and has_name:
                    boundaries.append((start, i))
            else:
                i += 1
        return boundaries