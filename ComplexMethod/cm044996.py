def upsert_context_section(
        self,
        project_root: Path,
        plan_path: str = "",
    ) -> Path | None:
        """Create or update the managed section in the agent context file.

        If the context file does not exist it is created with just the
        managed section.  If it exists, the content between
        ``<!-- SPECKIT START -->`` and ``<!-- SPECKIT END -->`` markers
        is replaced (or appended when no markers are found).

        Returns the path to the context file, or ``None`` when
        ``context_file`` is not set.
        """
        if not self.context_file:
            return None

        ctx_path = project_root / self.context_file
        section = (
            f"{self.CONTEXT_MARKER_START}\n"
            f"{self._build_context_section(plan_path)}\n"
            f"{self.CONTEXT_MARKER_END}\n"
        )

        if ctx_path.exists():
            content = ctx_path.read_text(encoding="utf-8-sig")
            start_idx = content.find(self.CONTEXT_MARKER_START)
            end_idx = content.find(
                self.CONTEXT_MARKER_END,
                start_idx if start_idx != -1 else 0,
            )

            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                # Replace existing section (include the end marker + newline)
                end_of_marker = end_idx + len(self.CONTEXT_MARKER_END)
                # Consume trailing line ending (CRLF or LF)
                if end_of_marker < len(content) and content[end_of_marker] == "\r":
                    end_of_marker += 1
                if end_of_marker < len(content) and content[end_of_marker] == "\n":
                    end_of_marker += 1
                new_content = content[:start_idx] + section + content[end_of_marker:]
            elif start_idx != -1:
                # Corrupted: start marker without end — replace from start through EOF
                new_content = content[:start_idx] + section
            elif end_idx != -1:
                # Corrupted: end marker without start — replace BOF through end marker
                end_of_marker = end_idx + len(self.CONTEXT_MARKER_END)
                if end_of_marker < len(content) and content[end_of_marker] == "\r":
                    end_of_marker += 1
                if end_of_marker < len(content) and content[end_of_marker] == "\n":
                    end_of_marker += 1
                new_content = section + content[end_of_marker:]
            else:
                # No markers found — append
                if content:
                    if not content.endswith("\n"):
                        content += "\n"
                    new_content = content + "\n" + section
                else:
                    new_content = section

            # Ensure .mdc files have required YAML frontmatter
            if ctx_path.suffix == ".mdc":
                new_content = self._ensure_mdc_frontmatter(new_content)
        else:
            ctx_path.parent.mkdir(parents=True, exist_ok=True)
            # Cursor .mdc files require YAML frontmatter to be loaded
            if ctx_path.suffix == ".mdc":
                new_content = self._ensure_mdc_frontmatter(section)
            else:
                new_content = section

        normalized = new_content.replace("\r\n", "\n").replace("\r", "\n")
        ctx_path.write_bytes(normalized.encode("utf-8"))
        return ctx_path