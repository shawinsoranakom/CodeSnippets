def _fix_incomplete_tag_in_chunk(self, chunk: str) -> str:
        """
        Fallback: fix incomplete <parameter=xxx or <function=xxx tags
        (missing >)
        Examples: <parameter=-C: -> <parameter=-C>, <parameter=parameter=-n:
        -> <parameter=-n>
        Also handles missing = cases: <function xxx> -> <function=xxx>,
        <functionxxx> -> <function=xxx>
        Only fixes tags that pass validation (parameter exists in tool definition)
        """
        # First, handle missing = cases for function tags
        chunk = self._fix_missing_equals_in_function_tag(chunk)

        for tag_type in ["parameter", "function"]:
            pattern = f"<{tag_type}="
            if pattern not in chunk:
                continue

            start_idx = chunk.find(pattern)
            after_tag = chunk[start_idx:]
            gt_pos = after_tag.find(">")
            lt_pos = after_tag.find("<", len(pattern))

            # Skip if already well-formed
            if (
                gt_pos != -1
                and (lt_pos == -1 or gt_pos < lt_pos)
                and pattern in after_tag[:gt_pos]
            ):
                continue

            # Extract tag name (stop at space, newline, or <)
            content = chunk[start_idx + len(pattern) :]
            end_pos = next(
                (i for i, ch in enumerate(content) if ch in (" ", "\n", "<")),
                len(content),
            )
            tag_name = content[:end_pos]

            if not tag_name:
                continue

            # Remove duplicate prefix: <parameter=parameter=xxx -> <parameter=xxx
            if tag_name.startswith(f"{tag_type}="):
                tag_name = tag_name[len(tag_type) + 1 :]

            # Remove trailing non-alphanumeric chars (keep - and _)
            while tag_name and not (
                tag_name[-1].isalnum() or tag_name[-1] in ("-", "_")
            ):
                tag_name = tag_name[:-1]

            if not tag_name:
                continue

            # Validate parameter exists in tool definition
            if tag_type == "parameter" and not self._validate_parameter_name(tag_name):
                continue

            # Apply fix
            chunk = chunk.replace(
                f"<{tag_type}={content[:end_pos]}", f"<{tag_type}={tag_name}>", 1
            )

        return chunk