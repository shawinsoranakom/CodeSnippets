def _query_path(self, data: Any, path: str) -> Any:
        """Query JSON data using a dot-notation path with array support.

        Args:
            data: The data to query
            path: Path like "users[0].name" or "config.settings.enabled"

        Returns:
            The value at the path
        """
        import re

        if not path:
            return data

        # Split path into segments, handling array notation
        segments = []
        for part in path.split("."):
            # Handle array notation like "users[0]"
            array_match = re.match(r"^(\w+)\[(\d+)\]$", part)
            if array_match:
                segments.append(array_match.group(1))
                segments.append(int(array_match.group(2)))
            elif part.isdigit():
                segments.append(int(part))
            else:
                segments.append(part)

        result = data
        for segment in segments:
            try:
                if isinstance(segment, int):
                    result = result[segment]
                elif isinstance(result, dict):
                    result = result[segment]
                elif isinstance(result, list) and segment.isdigit():
                    result = result[int(segment)]
                else:
                    raise DataProcessingError(
                        f"Cannot access '{segment}' on {type(result).__name__}"
                    )
            except (KeyError, IndexError, TypeError) as e:
                raise DataProcessingError(f"Path query failed at '{segment}': {e}")

        return result