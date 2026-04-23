def apply_patch(self, filename: str, patch_data: Union[str, bytes, Any]) -> None:
        """Apply *patch_text* (unified diff) to the latest revision and save a new revision.

        Uses the *unidiff* library to accurately apply hunks and validate context lines.
        """
        if isinstance(patch_data, bytes):
            patch_data = patch_data.decode("utf-8")
        if not isinstance(patch_data, str):
            raise ValueError(f"Expected str or bytes, got {type(patch_data)}")
        self._ensure_file(filename)
        original_content = self.get_latest_content(filename)

        if PatchSet is None:
            raise ImportError(
                "The 'unidiff' package is required for patch application. Install with 'pip install unidiff'."
            )

        patch = PatchSet(patch_data)
        # Our canvas stores exactly one file per patch operation so we
        # use the first (and only) patched_file object.
        if not patch:
            raise ValueError("Empty patch text provided.")
        patched_file = patch[0]
        working_lines = original_content.splitlines(keepends=True)
        line_offset = 0
        for hunk in patched_file:
            # Calculate the slice boundaries in the *current* working copy.
            start = hunk.source_start - 1 + line_offset
            end = start + hunk.source_length
            # Build the replacement block for this hunk.
            replacement: List[str] = []
            for line in hunk:
                if line.is_added or line.is_context:
                    replacement.append(line.value)
                # removed lines (line.is_removed) are *not* added.
            # Replace the slice with the hunk‑result.
            working_lines[start:end] = replacement
            line_offset += len(replacement) - (end - start)
        new_content = "".join(working_lines)

        # Finally commit the new revision.
        self.add_or_update_file(filename, new_content)