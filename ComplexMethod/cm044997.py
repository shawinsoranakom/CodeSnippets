def remove_context_section(self, project_root: Path) -> bool:
        """Remove the managed section from the agent context file.

        Returns ``True`` if the section was found and removed.  If the
        file becomes empty (or whitespace-only) after removal it is
        deleted.
        """
        if not self.context_file:
            return False

        ctx_path = project_root / self.context_file
        if not ctx_path.exists():
            return False

        content = ctx_path.read_text(encoding="utf-8-sig")
        start_idx = content.find(self.CONTEXT_MARKER_START)
        end_idx = content.find(
            self.CONTEXT_MARKER_END,
            start_idx if start_idx != -1 else 0,
        )

        # Only remove a complete, well-ordered managed section. If either
        # marker is missing, leave the file unchanged to avoid deleting
        # unrelated user-authored content.
        if start_idx == -1 or end_idx == -1 or end_idx <= start_idx:
            return False

        removal_start = start_idx
        removal_end = end_idx + len(self.CONTEXT_MARKER_END)

        # Consume trailing line ending (CRLF or LF)
        if removal_end < len(content) and content[removal_end] == "\r":
            removal_end += 1
        if removal_end < len(content) and content[removal_end] == "\n":
            removal_end += 1

        # Also strip a blank line before the section if present
        if removal_start > 0 and content[removal_start - 1] == "\n":
            if removal_start > 1 and content[removal_start - 2] == "\n":
                removal_start -= 1

        new_content = content[:removal_start] + content[removal_end:]

        # Normalize line endings before comparisons
        normalized = new_content.replace("\r\n", "\n").replace("\r", "\n")

        # For .mdc files, treat Speckit-generated frontmatter-only content as empty
        if ctx_path.suffix == ".mdc":
            import re
            # Delete the file if only YAML frontmatter remains (no body content)
            frontmatter_only = re.match(
                r"^---\n.*?\n---\s*$", normalized, re.DOTALL
            )
            if not normalized.strip() or frontmatter_only:
                ctx_path.unlink()
                return True

        if not normalized.strip():
            ctx_path.unlink()
        else:
            ctx_path.write_bytes(normalized.encode("utf-8"))

        return True